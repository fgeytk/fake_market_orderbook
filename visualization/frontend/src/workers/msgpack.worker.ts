import { decode } from '@msgpack/msgpack';

self.onmessage = (e: MessageEvent) => {
  const { data, id } = e.data;
  
  try {
    const decoded = decode(data);
    self.postMessage({ id, result: decoded });
  } catch (error) {
    self.postMessage({ id, error: (error as Error).message });
  }
};
