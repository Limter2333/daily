import 'axios';

declare module 'axios' {
  interface InternalAxiosRequestConfig {
    metadata?: {
      startTime: number;
    };
  }

  interface AxiosRequestConfig {
    metadata?: {
      startTime: number;
    };
  }
}
