# Pull Request

## Description

<!-- Provide a brief description of the changes in this PR -->

## Type of Change

<!-- Mark the relevant option with an "x" -->

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring
- [ ] CI/CD improvement
- [ ] Dependency update

## Related Issue(s)

<!-- Link to related issues using #issue_number -->

Closes #
Related to #

## Changes Made

<!-- List the main changes in this PR -->

-
-
-

## Testing

<!-- Describe the tests you ran and how to reproduce them -->

### Test Configuration

- **Python version:**
- **Node version:**
- **Database:** PostgreSQL with pgvector
- **OS:**

### Test Results

- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

```bash
# Commands used for testing
make test
# or
pytest packages/py-core/tests -v
cd apps/frontend && pnpm test
```

## Checklist

<!-- Mark completed items with an "x" -->

### Code Quality

- [ ] My code follows the project's code style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] My changes generate no new warnings or errors
- [ ] I have run linters (black, ruff, mypy, eslint)

### Testing

- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] I have added integration tests where appropriate
- [ ] Test coverage has not decreased

### Documentation

- [ ] I have updated the documentation accordingly
- [ ] I have updated the CHANGELOG.md file
- [ ] I have added docstrings to new functions/classes
- [ ] README.md has been updated if needed

### Security

- [ ] I have reviewed my code for security vulnerabilities
- [ ] No secrets or sensitive data are committed
- [ ] Dependencies have been scanned for vulnerabilities
- [ ] Input validation has been implemented where needed

### Database

- [ ] Database migrations have been created if needed
- [ ] Migrations have been tested (upgrade and downgrade)
- [ ] Database indexes have been considered for performance

### Performance

- [ ] I have considered the performance impact of my changes
- [ ] No N+1 queries introduced
- [ ] Caching strategy considered where appropriate

## Screenshots / Videos

<!-- If applicable, add screenshots or videos to demonstrate the changes -->

## Additional Notes

<!-- Add any additional context about the PR here -->

## Reviewer Notes

<!-- Special instructions for reviewers -->

---

## For Reviewers

### Review Checklist

- [ ] Code follows project conventions and best practices
- [ ] Changes are well-tested
- [ ] Documentation is clear and complete
- [ ] No obvious security issues
- [ ] Performance considerations addressed
- [ ] Breaking changes are clearly documented

### Suggested Reviewers

@cLeffNote44

---

**By submitting this pull request, I confirm that my contribution is made under the terms of the MIT License.**
