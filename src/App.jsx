
import React, { useEffect, useState, useRef } from "react";
import Chart from "chart.js/auto";
import { jsPDF } from "jspdf";

// Portfolio Chart Component with Dune-style styling
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
            borderColor: "#8B5CF6",
            backgroundColor: "rgba(139, 92, 246, 0.1)",
            fill: true,
            tension: 0.4,
            borderWidth: 3,
            pointBackgroundColor: "#8B5CF6",
            pointBorderColor: "#ffffff",
            pointBorderWidth: 2,
            pointRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
        },
        scales: {
          x: {
            grid: {
              color: "rgba(255, 255, 255, 0.1)",
              borderColor: "rgba(255, 255, 255, 0.1)",
            },
            ticks: {
              color: "#9CA3AF",
            },
          },
          y: {
            beginAtZero: false,
            grid: {
              color: "rgba(255, 255, 255, 0.1)",
              borderColor: "rgba(255, 255, 255, 0.1)",
            },
            ticks: {
              color: "#9CA3AF",
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

// Asset Details Modal with Dune styling
const AssetModal = ({ asset, onClose, onUpdateNotes, isEditor }) => {
  const [notes, setNotes] = useState(asset?.notes || "");

  if (!asset) return null;

  const handleSave = () => {
    onUpdateNotes(asset.id, notes);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-700 p-6 rounded-xl max-w-md w-full m-4">
        <h2 className="text-xl font-bold mb-4 text-white">{asset.name}</h2>
        <div className="space-y-3 mb-4">
          <div className="flex justify-between">
            <span className="text-gray-400">Balance:</span>
            <span className="text-white font-mono">{asset.balance} {asset.symbol}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Value:</span>
            <span className="text-green-400 font-mono">${asset.valueUSD.toLocaleString()}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">Price:</span>
            <span className="text-white font-mono">${asset.priceUSD.toFixed(4)}</span>
          </div>
        </div>
        {isEditor && (
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2 text-gray-300">Notes:</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:border-purple-500 focus:outline-none"
              rows="3"
              placeholder="Add your notes here..."
            />
          </div>
        )}
        <div className="flex space-x-3">
          {isEditor && (
            <button
              onClick={handleSave}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium"
            >
              Save
            </button>
          )}
          <button
            onClick={onClose}
            className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors font-medium"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// Report Generator Component with Dune styling
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
          className="bg-purple-600 text-white px-3 py-1.5 rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
        >
          Export {period}
        </button>
      ))}
    </div>
  );
};

// Main App Component with Dune.com styling
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
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">D</span>
              </div>
              <h1 className="text-2xl font-bold">Crypto Fund Analytics</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button className="text-gray-400 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-5 5v-5z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7H4l5-5v5z" />
                </svg>
              </button>
              <button className="text-gray-400 hover:text-white transition-colors">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-6">
        {/* Editor Access */}
        {!isEditor && (
          <div className="bg-gray-900 border border-gray-700 p-6 rounded-xl mb-6 max-w-md">
            <h2 className="text-lg font-semibold mb-4 text-purple-400">🔐 Editor Access</h2>
            <div className="space-y-4">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter access key"
                className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:border-purple-500 focus:outline-none"
                onKeyPress={(e) => e.key === "Enter" && checkPassword()}
              />
              <button
                onClick={checkPassword}
                className="w-full bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium"
              >
                Unlock Dashboard
              </button>
            </div>
          </div>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-900 border border-gray-700 p-6 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">Total Value</h3>
              <div className="w-2 h-2 bg-green-400 rounded-full"></div>
            </div>
            <p className="text-2xl font-bold text-white font-mono">
              ${totalValue.toLocaleString()}
            </p>
            <p className="text-sm text-green-400 mt-1">+2.4% (24h)</p>
          </div>
          
          <div className="bg-gray-900 border border-gray-700 p-6 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">Assets</h3>
              <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
            </div>
            <p className="text-2xl font-bold text-white font-mono">
              {visibleAssets.length}
            </p>
            <p className="text-sm text-gray-400 mt-1">Active positions</p>
          </div>

          <div className="bg-gray-900 border border-gray-700 p-6 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">Top Asset</h3>
              <div className="w-2 h-2 bg-purple-400 rounded-full"></div>
            </div>
            <p className="text-2xl font-bold text-white">
              ETH
            </p>
            <p className="text-sm text-gray-400 mt-1">83.6% of portfolio</p>
          </div>

          <div className="bg-gray-900 border border-gray-700 p-6 rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wide">Performance</h3>
              <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
            </div>
            <p className="text-2xl font-bold text-green-400 font-mono">
              +5.6%
            </p>
            <p className="text-sm text-gray-400 mt-1">Since inception</p>
          </div>
        </div>

        {/* Chart Section */}
        <div className="bg-gray-900 border border-gray-700 p-6 rounded-xl mb-8">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold text-white">Portfolio Performance</h3>
            <div className="flex space-x-2">
              <button className="px-3 py-1 text-xs bg-purple-600 text-white rounded-md">7D</button>
              <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600">30D</button>
              <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600">90D</button>
              <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600">1Y</button>
            </div>
          </div>
          <div className="chart-container">
            <PortfolioChart data={portfolioData.balanceHistory} />
          </div>
        </div>

        {/* Assets Table */}
        <div className="bg-gray-900 border border-gray-700 rounded-xl overflow-hidden mb-8">
          <div className="flex justify-between items-center p-6 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">Asset Holdings</h3>
            {isEditor && (
              <ReportGenerator portfolioData={portfolioData} />
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800">
                <tr>
                  <th className="text-left p-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Asset</th>
                  <th className="text-right p-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Balance</th>
                  <th className="text-right p-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Price</th>
                  <th className="text-right p-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Value</th>
                  <th className="text-right p-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Weight</th>
                  {isEditor && <th className="text-right p-4 text-xs font-medium text-gray-400 uppercase tracking-wide">Actions</th>}
                </tr>
              </thead>
              <tbody>
                {visibleAssets.map((asset, index) => (
                  <tr
                    key={asset.id}
                    className={`border-b border-gray-800 hover:bg-gray-800/50 cursor-pointer transition-colors ${
                      index % 2 === 0 ? 'bg-gray-900/50' : ''
                    }`}
                    onClick={() => setSelectedAsset(asset)}
                  >
                    <td className="p-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold text-xs">{asset.symbol.slice(0, 2)}</span>
                        </div>
                        <div>
                          <div className="font-medium text-white">{asset.name}</div>
                          <div className="text-sm text-gray-400">{asset.symbol}</div>
                        </div>
                      </div>
                    </td>
                    <td className="text-right p-4">
                      <div className="font-mono text-white">{asset.balance}</div>
                      <div className="text-sm text-gray-400">{asset.symbol}</div>
                    </td>
                    <td className="text-right p-4">
                      <div className="font-mono text-white">${asset.priceUSD.toLocaleString()}</div>
                    </td>
                    <td className="text-right p-4">
                      <div className="font-mono text-white">${asset.valueUSD.toLocaleString()}</div>
                    </td>
                    <td className="text-right p-4">
                      <div className="font-mono text-gray-300">
                        {((asset.valueUSD / totalValue) * 100).toFixed(1)}%
                      </div>
                    </td>
                    {isEditor && (
                      <td className="text-right p-4">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleHiddenAsset(asset.id);
                          }}
                          className="text-sm bg-red-600/20 text-red-400 px-3 py-1 rounded-md hover:bg-red-600/30 transition-colors border border-red-600/30"
                        >
                          Hide
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Hidden Assets */}
        {hiddenAssets.length > 0 && isEditor && (
          <div className="bg-gray-900 border border-gray-700 p-6 rounded-xl">
            <h3 className="text-lg font-semibold mb-4 text-white">Hidden Assets</h3>
            <div className="space-y-3">
              {portfolioData.assets
                .filter((asset) => hiddenAssets.includes(asset.id))
                .map((asset) => (
                  <div
                    key={asset.id}
                    className="flex justify-between items-center p-3 bg-gray-800 rounded-lg border border-gray-700"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-bold text-xs">{asset.symbol.slice(0, 2)}</span>
                      </div>
                      <span className="text-white font-medium">{asset.name}</span>
                    </div>
                    <button
                      onClick={() => toggleHiddenAsset(asset.id)}
                      className="text-sm bg-green-600/20 text-green-400 px-3 py-1 rounded-md hover:bg-green-600/30 transition-colors border border-green-600/30"
                    >
                      Show
                    </button>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Asset Modal */}
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
