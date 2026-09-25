// PulseMesh Gateway Entry Point
import { createServer } from './gateway/server.js';
import { config } from './config.js';

const { server, closeGracefully } = createServer();

server.listen(config.port, () => {
  console.log(`[PULSEMESH] Zero-Trust Agent Gateway listening on port ${config.port}`);
  console.log(`[PULSEMESH] SQLite WAL mode: ${config.db.journalMode} | sync: ${config.db.synchronous}`);
});

// POSIX Graceful Termination
const handleSignal = async (signal) => {
  console.log(`[PULSEMESH] Received ${signal}. Initiating graceful drain...`);
  await closeGracefully();
  console.log('[PULSEMESH] Clean drain complete. Exiting.');
  process.exit(0);
};

process.on('SIGTERM', () => handleSignal('SIGTERM'));
process.on('SIGINT', () => handleSignal('SIGINT'));
