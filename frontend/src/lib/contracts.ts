// Contract addresses on Mantle Sepolia Testnet
// Update these after deployment

export const CONTRACTS = {
  agentIdentity: "0x0000000000000000000000000000000000000000",
  tradeRegistry: "0x0000000000000000000000000000000000000000",
  arenaLeaderboard: "0x0000000000000000000000000000000000000000",
  reputationFeed: "0x0000000000000000000000000000000000000000",
} as const;

export const MANTLE_SEPOLIA = {
  chainId: 5003,
  rpcUrl: "https://rpc.sepolia.mantle.xyz",
  explorer: "https://explorer.sepolia.mantle.xyz",
} as const;
