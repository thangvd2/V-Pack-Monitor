const API_BASE = (() => {
  const ports = ['3000', '3001', '5173'];
  const currentPort = window.location.port;
  if (ports.includes(currentPort)) {
    return '';
  }
  return `${window.location.protocol}//${window.location.host}`;
})();

export default API_BASE;
