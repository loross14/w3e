import React, { useEffect, useState, useRef } from "react";
import Chart from "chart.js/auto";
import bcrypt from "bcryptjs";
import { createAlchemyWeb3 } from "@alch/alchemy-web3";
import { jsPDF } from "jspdf";

// Initialize Alchemy Web3 for Ethereum and Solana
const web3 = createAlchemyWeb3(
  "https://eth-mainnet.g.alchemy.com/v2/JlWnUY62Jlfn4RVNBULaIwZN916B58SA",
); // Replace with your Alchemy API key
const solanaWeb3 = createAlchemyWeb3(
  "https://solana-mainnet.g.alchemy.com/v2/JlWnUY62Jlfn4RVNBULaIwZN916B58SA",
); // Replace with your Alchemy API key

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

  // Hashed password for "bullrun"
  const hashedPassword =
    "$2a$10$6s9QzX7Y8v2j2z2Qz2z2Qz2z2Qz2z2Qz2z2Qz2z2Qz2z2Qz2z2Qz2";

  const checkPassword = () => {
    if (bcrypt.compareSync(password, hashedPassword)) {
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
      // Ethereum wallet data
      const ethBalance = await web3.eth.getBalance(
        "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
      );
      const ethTokens = await web3.alchemy.getTokenBalances(
        "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
      );
      const ethNfts = await web3.alchemy.getNfts({
        owner: "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
      });

      // Solana wallet data
      const solBalance = await solanaWeb3.getBalance(
        "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb",
      );
      const solTokens = await solanaWeb3.getTokenAccountsByOwner(
        "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb",
        {
          programId: "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        },
      );

      // Mock price data (replace with CoinGecko or Alchemy price API)
      const prices = {
        ETH: 3500,
        SOL: 150,
        // Add more token prices as needed
      };

      // Process assets
      const assets = [
        ...ethTokens.tokenBalances.map((token, i) => ({
          id: `eth-token-${i}`,
          type: "token",
          name: token.contractAddress.slice(0, 6), // Replace with token metadata
          amount: parseFloat(web3.utils.fromWei(token.tokenBalance, "ether")),
          valueUSD:
            parseFloat(web3.utils.fromWei(token.tokenBalance, "ether")) *
            prices.ETH,
          wallet: "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
          notes: "",
        })),
        ...ethNfts.ownedNfts.map((nft, i) => ({
          id: `eth-nft-${i}`,
          type: "nft",
          name: nft.metadata.name || `NFT #${i}`,
          valueUSD: 50000, // Mock value, replace with real valuation
          wallet: "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
          image: nft.metadata.image || "https://via.placeholder.com/150",
          notes: "",
        })),
        ...solTokens.value.map((token, i) => ({
          id: `sol-token-${i}`,
          type: "token",
          name: token.account.data.parsed.info.mint.slice(0, 6), // Replace with token metadata
          amount: token.account.data.parsed.info.tokenAmount.uiAmount,
          valueUSD:
            token.account.data.parsed.info.tokenAmount.uiAmount * prices.SOL,
          wallet: "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb",
          notes: "",
        })),
      ];

      // Calculate historical balance (mocked for simplicity)
      const balanceHistory = [
        {
          date: new Date().toISOString().split("T")[0],
          value:
            parseFloat(web3.utils.fromWei(ethBalance, "ether")) * prices.ETH +
            (solBalance.lamports / 1e9) * prices.SOL,
        },
        // Add more historical data points using Alchemy's historical APIs
      ];

      setPortfolioData({ balanceHistory, assets });
    } catch (error) {
      console.error("Error fetching portfolio data:", error);
      alert("Failed to update portfolio. Please try again.");
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
