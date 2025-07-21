import React, { useEffect, useState, useRef } from "react";
import Chart from "chart.js/auto";
import { Alchemy, Network } from "alchemy-sdk";
import { jsPDF } from "jspdf";

// Portfolio Chart Component
const PortfolioChart = ({ data }) => {
  const chartRef = useRef(null);
  const chartInstance = useRef(null);

  useEffect(() => {
    if (chartInstance.current) {
      chartInstance.current.destroy();
    }

    const ctx = chartRef.current.getContext("2d");
    chartInstance.current = new Chart(ctx, {
      type: "line",
      data: {
        labels: data.map((_, i) => `Day ${i + 1}`),
        datasets: [
          {
            label: "Portfolio Value",
            data: data.map((item) => item.value),
            borderColor: "rgb(16, 185, 129)",
            backgroundColor: "rgba(16, 185, 129, 0.1)",
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: false,
            ticks: {
              callback: (value) => `$${value.toLocaleString()}`,
            },
          },
        },
      },
    });

    return () => {
      if (chartInstance.current) {
        chartInstance.current.destroy();
      }
    };
  }, [data]);

  return <canvas ref={chartRef} />;
};

// Asset Details Modal
const AssetModal = ({ asset, onClose, onUpdateNotes, isEditor }) => {
  const [notes, setNotes] = useState(asset?.notes || "");

  if (!asset) return null;

  const handleSave = () => {
    onUpdateNotes(asset.id, notes);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white p-6 rounded-lg max-w-md w-full m-4">
        <h2 className="text-xl font-bold mb-4">{asset.name}</h2>
        <div className="space-y-2 mb-4">
          <p>
            <strong>Balance:</strong> {asset.balance} {asset.symbol}
          </p>
          <p>
            <strong>Value:</strong> ${asset.valueUSD.toLocaleString()}
          </p>
          <p>
            <strong>Price:</strong> ${asset.priceUSD.toFixed(4)}
          </p>
        </div>
        {isEditor && (
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Notes:</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full p-2 border rounded"
              rows="3"
            />
          </div>
        )}
        <div className="flex space-x-2">
          {isEditor && (
            <button
              onClick={handleSave}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Save
            </button>
          )}
          <button
            onClick={onClose}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600"
          >
            Close
          </button>
        </div>
      </div>
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
      `Total Balance: $${portfolioData.balanceHistory[0]?.value.toLocaleString() || "0"}`,
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
    <div className="flex flex-wrap gap-2">
      {periods.map((period) => (
        <button
          key={period}
          onClick={() => generateReport(period)}
          className="bg-emerald-600 text-white px-4 py-2 rounded hover:bg-emerald-700 text-sm"
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
    balanceHistory: [
      { value: 1250000 },
      { value: 1275000 },
      { value: 1310000 },
      { value: 1280000 },
      { value: 1320000 },
    ],
    assets: [
      {
        id: 1,
        name: "Ethereum",
        symbol: "ETH",
        balance: 450.5,
        priceUSD: 2450.30,
        valueUSD: 1103385.15,
        notes: "",
      },
      {
        id: 2,
        name: "Bitcoin",
        symbol: "BTC",
        balance: 2.8,
        priceUSD: 43250.00,
        valueUSD: 121100.00,
        notes: "",
      },
      {
        id: 3,
        name: "Chainlink",
        symbol: "LINK",
        balance: 15000,
        priceUSD: 14.75,
        valueUSD: 221250.00,
        notes: "",
      },
    ],
  });

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

  const visibleAssets = portfolioData.assets.filter(
    (asset) => !hiddenAssets.includes(asset.id),
  );

  const totalValue = visibleAssets.reduce(
    (sum, asset) => sum + asset.valueUSD,
    0,
  );

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        <header className="mb-8">
          <h1 className="text-4xl font-bold mb-2">
            🏦 Crypto Fund Portfolio Dashboard
          </h1>
          <p className="text-gray-400">
            Professional crypto asset management interface
          </p>
        </header>

        {!isEditor && (
          <div className="bg-gray-800 p-6 rounded-lg mb-6 max-w-md">
            <h2 className="text-xl font-semibold mb-4">Editor Access</h2>
            <div className="space-y-4">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded text-white"
                onKeyPress={(e) => e.key === "Enter" && checkPassword()}
              />
              <button
                onClick={checkPassword}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
              >
                Access Editor Mode
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Total Portfolio Value</h3>
            <p className="text-3xl font-bold text-emerald-400">
              ${totalValue.toLocaleString()}
            </p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Active Assets</h3>
            <p className="text-3xl font-bold text-blue-400">
              {visibleAssets.length}
            </p>
          </div>
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">24h Change</h3>
            <p className="text-3xl font-bold text-green-400">+2.4%</p>
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg mb-8">
          <h3 className="text-xl font-semibold mb-4">Portfolio Performance</h3>
          <div className="chart-container">
            <PortfolioChart data={portfolioData.balanceHistory} />
          </div>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg mb-8">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold">Asset Holdings</h3>
            {isEditor && (
              <ReportGenerator portfolioData={portfolioData} />
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left p-2">Asset</th>
                  <th className="text-right p-2">Balance</th>
                  <th className="text-right p-2">Price</th>
                  <th className="text-right p-2">Value</th>
                  <th className="text-right p-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {visibleAssets.map((asset) => (
                  <tr
                    key={asset.id}
                    className="border-b border-gray-700 hover:bg-gray-700 cursor-pointer"
                    onClick={() => setSelectedAsset(asset)}
                  >
                    <td className="p-2">
                      <div>
                        <div className="font-semibold">{asset.name}</div>
                        <div className="text-sm text-gray-400">
                          {asset.symbol}
                        </div>
                      </div>
                    </td>
                    <td className="text-right p-2">
                      {asset.balance} {asset.symbol}
                    </td>
                    <td className="text-right p-2">
                      ${asset.priceUSD.toLocaleString()}
                    </td>
                    <td className="text-right p-2">
                      ${asset.valueUSD.toLocaleString()}
                    </td>
                    <td className="text-right p-2">
                      {isEditor && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleHiddenAsset(asset.id);
                          }}
                          className="text-sm bg-red-600 text-white px-2 py-1 rounded hover:bg-red-700"
                        >
                          Hide
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {hiddenAssets.length > 0 && isEditor && (
          <div className="bg-gray-800 p-6 rounded-lg">
            <h3 className="text-xl font-semibold mb-4">Hidden Assets</h3>
            <div className="space-y-2">
              {portfolioData.assets
                .filter((asset) => hiddenAssets.includes(asset.id))
                .map((asset) => (
                  <div
                    key={asset.id}
                    className="flex justify-between items-center p-2 bg-gray-700 rounded"
                  >
                    <span>{asset.name}</span>
                    <button
                      onClick={() => toggleHiddenAsset(asset.id)}
                      className="text-sm bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
                    >
                      Show
                    </button>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {selectedAsset && (
        <AssetModal
          asset={selectedAsset}
          onClose={() => setSelectedAsset(null)}
          onUpdateNotes={updateNotes}
          isEditor={isEditor}
        />
      )}
    </div>
  );
};

export default App;