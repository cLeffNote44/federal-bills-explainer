type Level = "debug" | "info" | "warn" | "error";

interface LogContext {
  [key: string]: unknown;
}

function emit(level: Level, message: string, context?: LogContext) {
  const entry = {
    level,
    time: new Date().toISOString(),
    message,
    ...(context ?? {}),
  };
  // Single-line JSON so log aggregators (Vercel, Netlify, Datadog, etc.) parse it cleanly.
  const fn =
    level === "error" ? console.error : level === "warn" ? console.warn : console.log;
  fn(JSON.stringify(entry));
}

function serializeError(err: unknown) {
  if (err instanceof Error) {
    return {
      name: err.name,
      message: err.message,
      stack: err.stack,
    };
  }
  return { message: String(err) };
}

export const logger = {
  debug(message: string, context?: LogContext) {
    if (process.env.NODE_ENV === "production") return;
    emit("debug", message, context);
  },
  info(message: string, context?: LogContext) {
    emit("info", message, context);
  },
  warn(message: string, context?: LogContext) {
    emit("warn", message, context);
  },
  error(message: string, error?: unknown, context?: LogContext) {
    emit("error", message, {
      ...(context ?? {}),
      error: error !== undefined ? serializeError(error) : undefined,
    });
  },
  /**
   * Returns a logger bound to a fixed context (e.g. a job id) so callers
   * don't have to pass it on every call.
   */
  child(base: LogContext) {
    return {
      debug: (m: string, c?: LogContext) => logger.debug(m, { ...base, ...c }),
      info: (m: string, c?: LogContext) => logger.info(m, { ...base, ...c }),
      warn: (m: string, c?: LogContext) => logger.warn(m, { ...base, ...c }),
      error: (m: string, e?: unknown, c?: LogContext) =>
        logger.error(m, e, { ...base, ...c }),
    };
  },
};
