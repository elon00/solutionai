# Solution AI Blockchain Integration

This directory contains the blockchain components for the Solution AI project, built on Algorand with world-class features including smart contracts, NFTs, and tokenized economy.

## 🚀 Features

- **SOLAI Token**: 21 trillion supply utility token
- **Smart Contracts**: Ticket management and NFT issuance
- **NFT Tickets**: Unique digital assets for premium tickets
- **Para Wallet Integration**: Seamless wallet connectivity
- **Decentralized Records**: Immutable ticket storage
- **Token Rewards**: Incentive system for users

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- Para Wallet browser extension
- Algorand testnet/mainnet account with ALGO

## 🛠️ Installation

1. Install Python dependencies:
```bash
pip install pyteal algosdk
```

2. Install Node.js dependencies (for frontend):
```bash
npm install @algo/para-wallet-connect
```

## 🚀 Deployment Steps

### 1. Create SOLAI Token

```bash
cd scripts
python create_token.py
```

- Update the MNEMONIC in the script with your 25-word seed phrase
- For mainnet, change ALGOD_ADDRESS to "https://mainnet-api.algonand.network"
- Note the Asset ID from the output

### 2. Deploy Smart Contract

```bash
cd scripts
python deploy_contract.py
```

- Update MNEMONIC and ALGOD_ADDRESS as above
- Note the App ID from the output

### 3. Update Frontend Configuration

Edit `frontend/app.js` and update:
- `APP_ID`: Set to your deployed contract App ID
- `TOKEN_ID`: Set to your SOLAI token Asset ID
- `ALGOD_SERVER`: Change to mainnet if deploying to production

### 4. Run the DApp

1. Start the backend:
```bash
cd ../backend
pip install -r requirements.txt
uvicorn main:app --reload
```

2. Open `frontend/index.html` in browser

3. Connect Para Wallet and test features

## 🔧 Configuration

### Tokenomics
- **Name**: Solution AI Token
- **Symbol**: SOLAI
- **Total Supply**: 21,000,000,000,000 (21 trillion)
- **Decimals**: 6
- **Distribution**: 
  - 40% Community rewards
  - 30% Development fund
  - 20% Marketing
  - 10% Team allocation

### Smart Contract Functions
- `create_ticket`: Store ticket hash on blockchain
- `issue_nft`: Create NFT for premium tickets
- `transfer`: Transfer SOLAI tokens

## 🛡️ Security

The smart contracts include:
- Input validation
- Access controls
- Reentrancy protection
- Overflow checks

For production deployment, conduct a professional audit.

## 🌐 Mainnet Deployment

1. Update all scripts to use mainnet endpoints
2. Test thoroughly on testnet
3. Fund deployment account with ALGO
4. Deploy token and contract
5. Update frontend with production IDs
6. Launch and monitor

## 📊 Monitoring

- Use Algorand Explorer to monitor transactions
- Track token distribution and usage
- Monitor smart contract calls

## 🤝 Support

For issues or questions:
- Check Algorand documentation
- Join Algorand Discord
- Contact the development team

## 📄 License

This blockchain integration is part of the Solution AI project.