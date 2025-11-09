"""Generate explanations for bills using local OSS models."""

import logging
from typing import Optional, Dict
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from rich.console import Console

from .types import BillDTO, ExplanationDTO
from .settings import get_settings

logger = logging.getLogger(__name__)
console = Console()


class ExplanationGenerator:
    """Generate plain language explanations for bills."""
    
    def __init__(self, model_name: str = "google/flan-t5-base", use_gpu: bool = False):
        """Initialize the explanation generator."""
        self.model_name = model_name
        self.device = 0 if use_gpu and torch.cuda.is_available() else -1
        self.pipeline = None
        self._initialize_model()
        
    def _initialize_model(self):
        """Initialize the model pipeline."""
        console.print(f"[bold yellow]Loading explanation model: {self.model_name}...[/bold yellow]")
        
        try:
            # Determine task type based on model
            if "t5" in self.model_name.lower():
                task = "text2text-generation"
            else:
                task = "text-generation"
                
            self.pipeline = pipeline(
                task,
                model=self.model_name,
                device=self.device,
                max_length=512,
                truncation=True
            )
            
            device_name = "GPU" if self.device >= 0 else "CPU"
            console.print(f"[bold green]Model loaded successfully on {device_name}[/bold green]")
            
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            raise
            
    def generate_explanation(self, bill: BillDTO) -> ExplanationDTO:
        """Generate explanation for a bill."""
        if not self.pipeline:
            raise RuntimeError("Model not initialized")
            
        # Create prompt
        prompt = self._create_prompt(bill)
        
        # Generate explanation
        try:
            result = self.pipeline(
                prompt,
                max_new_tokens=350,
                temperature=0.3,
                top_p=0.9,
                do_sample=True,
                num_return_sequences=1
            )
            
            # Extract generated text
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    generated_text = result[0].get("generated_text", "")
                    # For text-generation models, remove the prompt from output
                    if "text-generation" in str(self.pipeline.task):
                        generated_text = generated_text.replace(prompt, "").strip()
                else:
                    generated_text = str(result[0])
            else:
                generated_text = str(result)
                
            # Clean up the text
            explanation_text = self._clean_explanation(generated_text)
            
            # Parse sections if structured
            sections = self._parse_sections(explanation_text)
            
            # Calculate word count
            word_count = len(explanation_text.split())
            
            return ExplanationDTO(
                bill_external_id=bill.external_id,
                explanation_text=explanation_text,
                model_name=self.model_name,
                sections=sections,
                word_count=word_count
            )
            
        except Exception as e:
            logger.error(f"Failed to generate explanation for {bill.external_id}: {e}")
            # Return a basic fallback explanation
            fallback_text = self._create_fallback_explanation(bill)
            return ExplanationDTO(
                bill_external_id=bill.external_id,
                explanation_text=fallback_text,
                model_name=self.model_name,
                sections=None,
                word_count=len(fallback_text.split())
            )
            
    def _create_prompt(self, bill: BillDTO) -> str:
        """Create prompt for the model."""
        bill_info = f"Bill: {bill.title}"
        if bill.short_title:
            bill_info += f" ('{bill.short_title}')"
        if bill.summary:
            bill_info += f"\nSummary: {bill.summary[:500]}"
        if bill.policy_area:
            bill_info += f"\nPolicy Area: {bill.policy_area}"
        if bill.sponsor:
            bill_info += f"\nSponsor: {bill.sponsor}"
            
        prompt = f"""Explain this federal bill in plain language for citizens:

{bill_info}

Provide a clear explanation covering:
1. What it does: Main provisions and changes
2. Why it matters: Impact and importance
3. Who is affected: Groups or individuals impacted
4. Key details: Important numbers, dates, or requirements

Keep the explanation between 200-400 words, using simple language that anyone can understand.

Explanation:"""
        
        return prompt
        
    def _clean_explanation(self, text: str) -> str:
        """Clean up generated explanation text."""
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove any remaining prompt artifacts
        if "Explanation:" in text:
            text = text.split("Explanation:", 1)[-1].strip()
            
        # Ensure proper sentence ending
        if text and not text[-1] in ".!?":
            text += "."
            
        return text
        
    def _parse_sections(self, text: str) -> Optional[Dict[str, str]]:
        """Parse explanation into sections if structured."""
        sections = {}
        
        # Look for numbered sections
        section_markers = [
            "1. What it does:",
            "2. Why it matters:",
            "3. Who is affected:",
            "4. Key details:"
        ]
        
        for i, marker in enumerate(section_markers):
            if marker.lower() in text.lower():
                start = text.lower().index(marker.lower()) + len(marker)
                # Find end (next section or end of text)
                end = len(text)
                if i < len(section_markers) - 1:
                    next_marker = section_markers[i + 1]
                    if next_marker.lower() in text.lower():
                        end = text.lower().index(next_marker.lower())
                        
                section_text = text[start:end].strip()
                section_name = marker.split(":")[0].replace(f"{i+1}. ", "")
                sections[section_name] = section_text
                
        return sections if sections else None
        
    def _create_fallback_explanation(self, bill: BillDTO) -> str:
        """Create a basic fallback explanation."""
        explanation = f"This bill, titled '{bill.title}', "
        
        if bill.law_number:
            explanation += f"became Public Law {bill.law_number}. "
        else:
            explanation += "has been enacted into law. "
            
        if bill.summary:
            explanation += f"\n\n{bill.summary[:400]}"
        else:
            explanation += "\n\nThis legislation addresses important federal matters. "
            
        if bill.policy_area:
            explanation += f"\n\nIt falls under the policy area of {bill.policy_area}. "
            
        if bill.sponsor:
            explanation += f"The bill was sponsored by {bill.sponsor}. "
            
        explanation += "\n\nFor complete details, please refer to the full text of the legislation."
        
        return explanation
