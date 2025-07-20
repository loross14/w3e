
import React, { useState, useEffect, useRef } from 'react';
import { Alchemy, Network } from 'alchemy-sdk';
import { Chart, registerables } from 'chart.js';
import bcrypt from 'bcryptjs';
import { jsPDF } from 'jspdf';
import './App.css';

// Register Chart.js components
Chart.register(...registerables);

// Initialize Alchemy
const config = {
  apiKey: "JlWnUY62Jlfn4RVNBULaIwZN916B58SA", // Replace with your Alchemy API key
  network: Network.ETH_MAINNET,
};
const alchemy = new Alchemy(config);

// Mock data (replace with actual Alchemy API calls)
const mockPortfolioData = {
  balanceHistory: [
    { date: "2025-07-20", value: 1000000 },
    { date: "2025-07-19", value: 950000 },
    { date: "2025-07-18", value: 980000 },
  ],
  assets: [
    {
      id: "1",
      type: "token",
      name: "ETH",
      amount: 10,
      valueUSD: 35000,
      wallet: "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
      notes: "",
    },
    {
      id: "2",
      type: "nft",
      name: "CryptoPunk #1234",
      valueUSD: 50000,
      wallet: "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
      image: "https://via.placeholder.com/150",
      notes: "",
    },
    {
      id: "3",
      type: "token",
      name: "SOL",
      amount: 100,
      valueUSD: 15000,
      wallet: "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb",
      notes: "",
    },
  ],
};

// Portfolio Chart Component
const PortfolioChart = ({ data }) => {
  const canvasRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (chartRef.current) {
      chartRef.current.destroy();
    }

    const ctx = canvasRef.current.getContext("2d");
    chartRef.current = new Chart(ctx, {
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

    return () => {
      if (chartRef.current) {
        chartRef.current.destroy();
      }
    };
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
          <div
            key={asset.id}
            className="bg-gray-800 p-4 rounded-lg shadow"
          >
            <h3 className="text-lg font-semibold text-white">
              {asset.name}
            </h3>
            <p className="text-gray-300">Type: {asset.type}</p>
            <p className="text-gray-300">
              Value: ${asset.valueUSD.toLocaleString()}
            </p>
            <p className="text-gray-300">
              Wallet: {asset.wallet.slice(0, 6)}...
              {asset.wallet.slice(-4)}
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
const AssetDetail = ({ asset, updateNotes, isEditor, setSelectedAsset }) => {
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
      <p className="text-gray-300">
        Value: ${asset.valueUSD.toLocaleString()}
      </p>
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
        onClick={() => setSelectedAsset(null)}
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
export default function App() {
  const [isEditor, setIsEditor] = useState(false);
  const [password, setPassword] = useState("");
  const [hiddenAssets, setHiddenAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [portfolioData, setPortfolioData] = useState(mockPortfolioData);

  const hashedPassword = "$2a$10$6s9QzX7Y8v2j2z2Qz2z2Qz2z2Qz2z2Qz2z2Qz2z2Qz2z2Qz2z2Qz2"; // Hashed "bullrun"

  const checkPassword = () => {
    if (bcrypt.compareSync(password, hashedPassword)) {
      setIsEditor(true);
      setPassword("");
    } else {
      alert("Incorrect password");
    }
  };

  const toggleHiddenAsset = (assetId) => {
    setHiddenAssets((prev) =>
      prev.includes(assetId)
        ? prev.filter((id) => id !== assetId)
        : [...prev, assetId],
    );
  };

  const updateNotes = (assetId, notes) => {
    setPortfolioData((prev) => ({
      ...prev,
      assets: prev.assets.map((asset) =>
        asset.id === assetId ? { ...asset, notes } : asset,
      ),
    }));
  };

  // Fetch portfolio data (mocked for now)
  useEffect(() => {
    // Replace with actual Alchemy API calls
    // Example: alchemy.core.getBalance('0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98').then(balance => {...});
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-6">
        Crypto Fund Portfolio Dashboard
      </h1>
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
              setSelectedAsset={setSelectedAsset}
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
}
