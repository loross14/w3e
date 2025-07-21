import React, { useEffect, useState, useRef } from "react";
import Chart from "chart.js/auto";
import { Alchemy, Network } from "alchemy-sdk";
import { jsPDF } from "jspdf";

// Initialize Alchemy SDK for Ethereum
const config = {
  apiKey: "JlWnUY62Jlfn4RVNBULaIwZN916B58SA", // Replace with your Alchemy API key
  network: Network.ETH_MAINNET,
};
const alchemy = new Alchemy(config);

// Portfolio Chart Component
const PortfolioChart = ({ data }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const ctx = canvasRef.current.getContext("2d");
    const chart = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.map((d) => d.date),
        datasets: [
          {
            label: "Portfolio Value (USD)",
            data: data.map((d) => d.value),
            borderColor: "#10B981",
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
          mode: "index",
          intersect: false,
        },
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) =>
                `$${context.parsed.y.toLocaleString()} on ${context.label}`,
            },
          },
        },
      },
    });

    return () => chart.destroy();
  }, [data]);

  return <canvas ref={canvasRef} className="chart-container" />;
};

// Asset List Component
const AssetList = ({
  assets,
  hiddenAssets,
  toggleHiddenAsset,
  setSelectedAsset,
  isEditor,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {assets
        .filter((asset) => !hiddenAssets.includes(asset.id))
        .map((asset) => (
          <div key={asset.id} className="bg-gray-800 p-4 rounded-lg shadow">
            <h3 className="text-lg font-semibold text-white">{asset.name}</h3>
            <p className="text-gray-300">Type: {asset.type}</p>
            <p className="text-gray-300">
              Value: ${asset.valueUSD.toLocaleString()}
            </p>
            <p className="text-gray-300">
              Wallet: {asset.wallet.slice(0, 6)}...{asset.wallet.slice(-4)}
            </p>
            <button
              onClick={() => setSelectedAsset(asset)}
              className="mt-2 bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700"
            >
              View Details
            </button>
            {isEditor && (
              <button
                onClick={() => toggleHiddenAsset(asset.id)}
                className="mt-2 ml-2 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
              >
                {hiddenAssets.includes(asset.id) ? "Show" : "Hide"}
              </button>
            )}
          </div>
        ))}
    </div>
  );
};

// Asset Detail Component
const AssetDetail = ({ asset, updateNotes, isEditor }) => {
  if (!asset) return null;
  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow">
      <h2 className="text-2xl font-bold text-white mb-4">{asset.name}</h2>
      {asset.type === "nft" && (
        <img
          src={asset.image}
          alt={asset.name}
          className="w-32 h-32 mb-4 rounded"
        />
      )}
      <p className="text-gray-300">Type: {asset.type}</p>
      <p className="text-gray-300">Value: ${asset.valueUSD.toLocaleString()}</p>
      <p className="text-gray-300">Wallet: {asset.wallet}</p>
      {isEditor && (
        <div className="mt-4">
          <textarea
            className="w-full p-2 bg-gray-700 text-white rounded"
            value={asset.notes}
            onChange={(e) => updateNotes(asset.id, e.target.value)}
            placeholder="Add notes..."
          />
        </div>
      )}
      <button
        onClick={() => updateNotes(null, "")}
        className="mt-4 bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
      >
        Back to List
      </button>
    </div>
  );
};

// Report Generator Component
const ReportGenerator = ({ portfolioData }) => {
  const periods = ["1 Week", "1 Month", "1 Quarter", "1 Year"];

  const generateReport = (period) => {
    const doc = new jsPDF();
    doc.setFontSize(20);
    doc.text(`Crypto Fund Performance Report - ${period}`, 20, 20);
    doc.setFontSize(12);
    doc.text(
      `Total Balance: $${portfolioData.balanceHistory[0].value.toLocaleString()}`,
      20,
      40,
    );
    doc.text("Assets:", 20, 50);
    portfolioData.assets.forEach((asset, i) => {
      doc.text(
        `${asset.name}: $${asset.valueUSD.toLocaleString()}`,
        30,
        60 + i * 10,
      );
    });
    doc.save(`CryptoFund_Report_${period.replace(" ", "_")}.pdf`);
  };

  return (
    <div className="flex space-x-4">
      {periods.map((period) => (
        <button
          key={period}
          onClick={() => generateReport(period)}
          className="bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700"
        >
          Generate {period} Report
        </button>
      ))}
    </div>
  );
};

// Main App Component
const App = () => {
  const [isEditor, setIsEditor] = useState(false);
  const [password, setPassword] = useState("");
  const [hiddenAssets, setHiddenAssets] = useState(
    () => JSON.parse(localStorage.getItem("hiddenAssets")) || [],
  );
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [portfolioData, setPortfolioData] = useState({
    balanceHistory: [],
    assets: [],
  });
  const [isLoading, setIsLoading] = useState(false);

  // Simple password check for "bullrun"
  const correctPassword = "bullrun";

  const checkPassword = () => {
    if (password === correctPassword) {
      setIsEditor(true);
      setPassword("");
    } else {
      alert("Incorrect password");
    }
  };

  const toggleHiddenAsset = (assetId) => {
    setHiddenAssets((prev) => {
      const newHiddenAssets = prev.includes(assetId)
        ? prev.filter((id) => id !== assetId)
        : [...prev, assetId];
      localStorage.setItem("hiddenAssets", JSON.stringify(newHiddenAssets));
      return newHiddenAssets;
    });
  };

  const updateNotes = (assetId, notes) => {
    if (!assetId) {
      setSelectedAsset(null);
      return;
    }
    setPortfolioData((prev) => ({
      ...prev,
      assets: prev.assets.map((asset) =>
        asset.id === assetId ? { ...asset, notes } : asset,
      ),
    }));
  };

  // Fetch portfolio data
  const updatePortfolio = async () => {
    setIsLoading(true);
    try {
      // Mock wallet address for demo
      const walletAddress = "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98";
      
      // Ethereum wallet data using new Alchemy SDK
      const ethBalance = await alchemy.core.getBalance(walletAddress);
      const ethTokens = await alchemy.core.getTokenBalances(walletAddress);
      const ethNfts = await alchemy.nft.getNftsForOwner(walletAddress);

      // Mock price data (replace with CoinGecko or Alchemy price API)
      const prices = {
        ETH: 3500,
        SOL: 150,
      };

      // Process assets
      const assets = [
        // ETH Balance
        {
          id: 'eth-balance',
          type: "token",
          name: "Ethereum",
          amount: parseFloat(ethBalance._hex) / 1e18,
          valueUSD: (parseFloat(ethBalance._hex) / 1e18) * prices.ETH,
          wallet: walletAddress,
          notes: "",
        },
        // ERC-20 Tokens
        ...ethTokens.tokenBalances
          .filter(token => token.tokenBalance !== "0x0")
          .map((token, i) => ({
            id: `eth-token-${i}`,
            type: "token",
            name: token.contractAddress.slice(0, 6), 
            amount: parseInt(token.tokenBalance, 16) / 1e18,
            valueUSD: (parseInt(token.tokenBalance, 16) / 1e18) * 100, // Mock price
            wallet: walletAddress,
            notes: "",
          })),
        // NFTs
        ...ethNfts.ownedNfts.slice(0, 5).map((nft, i) => ({
          id: `eth-nft-${i}`,
          type: "nft",
          name: nft.title || `NFT #${i}`,
          valueUSD: 50000, // Mock value
          wallet: walletAddress,
          image: nft.media?.[0]?.gateway || "https://via.placeholder.com/150",
          notes: "",
        })),
      ];

      // Calculate historical balance (mocked for demo)
      const balanceHistory = [
        { date: "2024-01-01", value: 850000 },
        { date: "2024-02-01", value: 920000 },
        { date: "2024-03-01", value: 1100000 },
        { date: "2024-04-01", value: 1050000 },
        { date: "2024-05-01", value: 1200000 },
        { date: new Date().toISOString().split("T")[0], value: assets.reduce((sum, asset) => sum + asset.valueUSD, 0) },
      ];

      setPortfolioData({ balanceHistory, assets });
    } catch (error) {
      console.error("Error fetching portfolio data:", error);
      // Set mock data if API fails
      const mockData = {
        balanceHistory: [
          { date: "2024-01-01", value: 850000 },
          { date: "2024-02-01", value: 920000 },
          { date: "2024-03-01", value: 1100000 },
          { date: "2024-04-01", value: 1050000 },
          { date: "2024-05-01", value: 1200000 },
          { date: new Date().toISOString().split("T")[0], value: 1350000 },
        ],
        assets: [
          {
            id: 1,
            name: 'Bitcoin',
            type: 'token',
            valueUSD: 450000,
            wallet: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
            notes: 'Primary BTC holdings'
          },
          {
            id: 2,
            name: 'Ethereum',
            type: 'token',
            valueUSD: 320000,
            wallet: '0x742d35Cc6585C42161C0F57C0C5E6Ba5',
            notes: 'ETH position for DeFi'
          },
          {
            id: 3,
            name: 'Bored Ape #1234',
            type: 'nft',
            valueUSD: 85000,
            wallet: '0x742d35Cc6585C42161C0F57C0C5E6Ba5',
            image: 'https://via.placeholder.com/150',
            notes: 'Blue chip NFT'
          }
        ]
      };
      setPortfolioData(mockData);
    } finally {
      setIsLoading(false);
    }
  };

  // Initialize hidden assets from localStorage
  useEffect(() => {
    const storedHiddenAssets =
      JSON.parse(localStorage.getItem("hiddenAssets")) || [];
    setHiddenAssets(storedHiddenAssets);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">
        Crypto Fund Portfolio Dashboard
      </h1>
      <button
        onClick={updatePortfolio}
        disabled={isLoading}
        className={`mb-6 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        {isLoading ? "Updating..." : "Update Portfolio"}
      </button>
      {!isEditor && (
        <div className="mb-6">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="p-2 bg-gray-700 text-white rounded mr-2"
            placeholder="Enter password for editor view"
          />
          <button
            onClick={checkPassword}
            className="bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700"
          >
            Unlock Editor
          </button>
        </div>
      )}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {selectedAsset ? (
            <AssetDetail
              asset={selectedAsset}
              updateNotes={updateNotes}
              isEditor={isEditor}
            />
          ) : (
            <AssetList
              assets={portfolioData.assets}
              hiddenAssets={hiddenAssets}
              toggleHiddenAsset={toggleHiddenAsset}
              setSelectedAsset={setSelectedAsset}
              isEditor={isEditor}
            />
          )}
        </div>
        <div>
          <h2 className="text-xl font-semibold mb-4">Portfolio Value</h2>
          <PortfolioChart data={portfolioData.balanceHistory} />
        </div>
      </div>
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-4">Generate Reports</h2>
        <ReportGenerator portfolioData={portfolioData} />
      </div>
    </div>
  );
};

export default App;
