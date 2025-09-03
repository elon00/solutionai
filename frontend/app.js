document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('triage-form');
    const resultDiv = document.getElementById('result');
    const labelSpan = document.getElementById('label');
    const confidenceSpan = document.getElementById('confidence');
    const summarySpan = document.getElementById('summary');
    const loadRecentBtn = document.getElementById('load-recent');
    const recentListDiv = document.getElementById('recent-list');

    // Blockchain elements
    const connectWalletBtn = document.getElementById('connect-wallet');
    const walletInfo = document.getElementById('wallet-info');
    const walletAddress = document.getElementById('wallet-address');
    const tokenBalance = document.getElementById('token-balance');
    const createNftBtn = document.getElementById('create-nft');
    const claimRewardsBtn = document.getElementById('claim-rewards');
    const viewNftsBtn = document.getElementById('view-nfts');
    const nftResult = document.getElementById('nft-result');
    const nftId = document.getElementById('nft-id');
    const nftTxLink = document.getElementById('nft-tx-link');

    // Blockchain configuration
    const ALGOD_SERVER = 'https://testnet-api.algonand.network';
    const ALGOD_TOKEN = '';
    const APP_ID = 987654321; // Deployed smart contract App ID
    const TOKEN_ID = 123456789; // Deployed SOLAI token Asset ID

    let paraWallet = null;
    let connectedAddress = null;

    // Connect Para Wallet
    async function connectWallet() {
        try {
            paraWallet = new ParaWalletConnect();
            const accounts = await paraWallet.connect();
            connectedAddress = accounts[0];
            walletAddress.textContent = connectedAddress;
            walletInfo.classList.remove('hidden');
            connectWalletBtn.textContent = 'Connected';
            connectWalletBtn.disabled = true;

            // Enable blockchain buttons
            createNftBtn.disabled = false;
            claimRewardsBtn.disabled = false;
            viewNftsBtn.disabled = false;

            // Load token balance
            await loadTokenBalance();
        } catch (error) {
            alert('Failed to connect wallet: ' + error.message);
        }
    }

    // Load SOLAI token balance
    async function loadTokenBalance() {
        if (!connectedAddress) return;

        try {
            const response = await fetch(`${ALGOD_SERVER}/v2/accounts/${connectedAddress}`, {
                headers: { 'X-Algo-API-Token': ALGOD_TOKEN }
            });
            const data = await response.json();
            const assets = data.assets || [];
            const solaiAsset = assets.find(asset => asset['asset-id'] === TOKEN_ID);
            const balance = solaiAsset ? solaiAsset.amount / 1000000 : 0; // Assuming 6 decimals
            tokenBalance.textContent = balance.toFixed(2);
        } catch (error) {
            console.error('Error loading balance:', error);
        }
    }

    // Create NFT for ticket
    async function createNFT() {
        if (!connectedAddress) {
            alert('Please connect your wallet first');
            return;
        }

        const ticketText = document.getElementById('ticket-text').value;
        if (!ticketText) {
            alert('Please classify a ticket first');
            return;
        }

        try {
            const ticketHash = btoa(ticketText).substring(0, 32); // Simple hash
            const txn = {
                type: 'appl',
                from: connectedAddress,
                appIndex: APP_ID,
                appArgs: ['issue_nft', ticketText, `https://solutionai.com/nft/${ticketHash}`],
                suggestedParams: await getSuggestedParams()
            };

            const signedTxn = await paraWallet.signTransaction([txn]);
            const txId = await sendTransaction(signedTxn[0]);

            nftId.textContent = 'Processing...';
            nftResult.classList.remove('hidden');

            // Wait for confirmation and get asset ID
            setTimeout(async () => {
                const assetId = await getCreatedAssetId(txId);
                nftId.textContent = assetId;
                nftTxLink.href = `https://testnet.algoexplorer.io/tx/${txId}`;
            }, 5000);

        } catch (error) {
            alert('Failed to create NFT: ' + error.message);
        }
    }

    // Helper functions
    async function getSuggestedParams() {
        const response = await fetch(`${ALGOD_SERVER}/v2/transactions/params`, {
            headers: { 'X-Algo-API-Token': ALGOD_TOKEN }
        });
        return await response.json();
    }

    async function sendTransaction(signedTxn) {
        const response = await fetch(`${ALGOD_SERVER}/v2/transactions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Algo-API-Token': ALGOD_TOKEN
            },
            body: JSON.stringify(signedTxn)
        });
        const data = await response.json();
        return data.txId;
    }

    async function getCreatedAssetId(txId) {
        // Simplified - in practice, parse transaction for inner txn
        return 'Asset ID will be shown here';
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const apiKey = document.getElementById('api-key').value;
        const ticketText = document.getElementById('ticket-text').value;

        try {
            const response = await fetch('http://localhost:8000/api/v1/triage', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Api-Key': apiKey
                },
                body: JSON.stringify({ ticket_text: ticketText })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            labelSpan.textContent = data.label;
            confidenceSpan.textContent = (data.confidence * 100).toFixed(2) + '%';
            summarySpan.textContent = data.summary;
            resultDiv.classList.remove('hidden');
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });

    loadRecentBtn.addEventListener('click', async () => {
        const apiKey = document.getElementById('api-key').value;
        if (!apiKey) {
            alert('Please enter your API key first');
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/api/v1/recent', {
                headers: {
                    'X-Api-Key': apiKey
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            recentListDiv.innerHTML = '';
            data.forEach(item => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'recent-item';
                itemDiv.innerHTML = `
                    <h4>${item.label} (${(item.confidence * 100).toFixed(2)}%)</h4>
                    <p><strong>Ticket:</strong> ${item.ticket_text}</p>
                    <p><strong>Summary:</strong> ${item.summary}</p>
                    <p><strong>Timestamp:</strong> ${new Date(item.timestamp).toLocaleString()}</p>
                `;
                recentListDiv.appendChild(itemDiv);
            });
        } catch (error) {
            alert('Error loading recent tickets: ' + error.message);
        }
    });

    // Blockchain event listeners
    connectWalletBtn.addEventListener('click', connectWallet);
    createNftBtn.addEventListener('click', createNFT);

    claimRewardsBtn.addEventListener('click', () => {
        alert('Token rewards feature coming soon!');
    });

    viewNftsBtn.addEventListener('click', () => {
        alert('NFT viewing feature coming soon!');
    });
});