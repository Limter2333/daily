/**
 * 前端日志模块 - 将日志输出到浏览器控制台
 * 可通过 API发送到后端日志系统
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  module: string;
  message: string;
  data?: unknown;
}

class Logger {
  private module: string;
  private static logs: LogEntry[] = [];
  private static maxLogs = 1000;
  private static enableConsole = true;
  private static enableRemote = false;
  private static remoteQueue: LogEntry[] = [];
  private static flushTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(module: string) {
    this.module = module;
  }

  private formatTimestamp(): string {
    const now = new Date();
    const pad = (n: number) => n.toString().padStart(2, '0');
    return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}.${now.getMilliseconds().toString().padStart(3, '0')}`;
  }

  private addLog(level: LogLevel, message: string, data?: unknown): void {
    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level,
      module: this.module,
      message,
      data,
    };

    // 添加到内存中的日志队列
    Logger.logs.push(entry);
    if (Logger.logs.length > Logger.maxLogs) {
      Logger.logs.shift();
    }

    // 输出到控制台
    if (Logger.enableConsole) {
      const prefix = `[${entry.timestamp}] [${level.toUpperCase()}] [${this.module}]`;
      const consoleArgs = data !== undefined ? [prefix, message, data] : [prefix, message];

      switch (level) {
        case 'debug':
          console.debug(...consoleArgs);
          break;
        case 'info':
          console.info(...consoleArgs);
          break;
        case 'warn':
          console.warn(...consoleArgs);
          break;
        case 'error':
          console.error(...consoleArgs);
          break;
      }
    }

    // 添加到远程队列
    if (Logger.enableRemote) {
      Logger.remoteQueue.push(entry);
      Logger.scheduleFlush();
    }
  }

  private static scheduleFlush(): void {
    if (Logger.flushTimer) return;

    Logger.flushTimer = setTimeout(() => {
      Logger.flush();
      Logger.flushTimer = null;
    }, 5000); // 每5秒批量发送一次
  }

  private static async flush(): Promise<void> {
    if (Logger.remoteQueue.length === 0) return;

    const logsToSend = [...Logger.remoteQueue];
    Logger.remoteQueue = [];

    try {
      await fetch('/api/logs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ logs: logsToSend }),
      });
    } catch (error) {
      // 发送失败，放回队列
      Logger.remoteQueue.unshift(...logsToSend);
      console.warn('Failed to send logs to backend:', error);
    }
  }

  debug(message: string, data?: unknown): void {
    this.addLog('debug', message, data);
  }

  info(message: string, data?: unknown): void {
    this.addLog('info', message, data);
  }

  warn(message: string, data?: unknown): void {
    this.addLog('warn', message, data);
  }

  error(message: string, data?: unknown): void {
    this.addLog('error', message, data);
  }

  /**
   * 获取所有日志（可用于调试或发送到后端）
   */
  static getLogs(): LogEntry[] {
    return [...Logger.logs];
  }

  /**
   * 清空日志
   */
  static clearLogs(): void {
    Logger.logs = [];
  }

  /**
   * 导出日志为 JSON字符串
   */
  static exportLogs(): string {
    return JSON.stringify(Logger.logs, null, 2);
  }

  /**
   * 启用/禁用控制台输出
   */
  static setConsoleEnabled(enabled: boolean): void {
    Logger.enableConsole = enabled;
  }

  /**
   * 启用/禁用远程日志
   */
  static setRemoteEnabled(enabled: boolean): void {
    Logger.enableRemote = enabled;
    if (enabled) {
      Logger.flush();
    }
  }

  /**
   * 手动刷新远程日志队列
   */
  static async flushRemote(): Promise<void> {
    await Logger.flush();
  }
}

/**
 * 创建日志实例
 * @param module 模块名称
 */
export function createLogger(module: string): Logger {
  return new Logger(module);
}

/**
 * 默认日志实例
 */
export const logger = createLogger('app');

export default logger;
