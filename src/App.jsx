import React, { useState, useRef, useEffect } from 'react';
import { Chart } from 'chart.js/auto';
import jsPDF from 'jspdf';
import bcrypt from 'bcryptjs';

// Mock data for demonstration
const mockPortfolioData = {
  balanceHistory: [
    { date: '2024-01-01', value: 850000 },
    { date: '2024-02-01', value: 920000 },
    { date: '2024-03-01', value: 1100000 },
    { date: '2024-04-01', value: 1050000 },
    { date: '2024-05-01', value: 1200000 },
    { date: '2024-06-01', value: 1350000 },
  ],
  assets: [
    {
      id: 1,
      name: 'Bitcoin',
      type: 'cryptocurrency',
      valueUSD: 450000,
      wallet: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
      notes: 'Primary BTC holdings'
    },
    {
      id: 2,
      name: 'Ethereum',
      type: 'cryptocurrency',
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
const AssetList = ({ assets, hiddenAssets, toggleHiddenAsset, setSelectedAsset, isEditor }) => {
  const visibleAssets = assets.filter(asset => !hiddenAssets.includes(asset.id));

  return (
    <div>
      <h2 className="text-xl font-semibold mb-4">Asset List</h2>
      <div className="space-y-4">
        {visibleAssets.map(asset => (
          <div key={asset.id} className="bg-gray-800 p-4 rounded-lg">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="font-semibold">{asset.name}</h3>
                <p className="text-gray-400">{asset.type}</p>
                <p className="text-green-400">${asset.valueUSD.toLocaleString()}</p>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => setSelectedAsset(asset)}
                  className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
                >
                  View Details
                </button>
                {isEditor && (
                  <button
                    onClick={() => toggleHiddenAsset(asset.id)}
                    className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                  >
                    Hide
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Asset Detail Component
const AssetDetail = ({ asset, updateNotes, isEditor, setSelectedAsset }) => {
  const [notes, setNotes] = useState(asset.notes || '');

  const handleSaveNotes = () => {
    updateNotes(asset.id, notes);
    alert('Notes saved!');
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg">
      <button
        onClick={() => setSelectedAsset(null)}
        className="mb-4 text-blue-400 hover:text-blue-300"
      >
        ← Back to Asset List
      </button>
      <h2 className="text-2xl font-bold mb-4">{asset.name}</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p className="text-gray-400 mb-2">Type: {asset.type}</p>
          <p className="text-gray-400 mb-2">Value: <span className="text-green-400">${asset.valueUSD.toLocaleString()}</span></p>
          <p className="text-gray-400 mb-4">Wallet: {asset.wallet}</p>
          {asset.image && (
            <img src={asset.image} alt={asset.name} className="w-32 h-32 rounded-lg" />
          )}
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-2">Notes</h3>
          {isEditor ? (
            <div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full p-2 bg-gray-700 text-white rounded mb-2"
                rows="4"
                placeholder="Add notes about this asset..."
              />
              <button
                onClick={handleSaveNotes}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
              >
                Save Notes
              </button>
            </div>
          ) : (
            <p className="text-gray-300">{asset.notes || 'No notes available'}</p>
          )}
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
  const [portfolioData, setPortfolioData] = useState(mockPortfolioData);
  const [selectedAsset, setSelectedAsset] = useState(null);

  // Sample hashed password (in production, this would come from a secure backend)
  const hashedPassword = "$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi"; // password

  const checkPassword = async () => {
    const isValid = await bcrypt.compare(password, hashedPassword);
    if (isValid) {
      setIsEditor(true);
    } else {
      alert('Incorrect password');
    }
  };

  const toggleHiddenAsset = (assetId) => {
    setHiddenAssets(prev => 
      prev.includes(assetId) 
        ? prev.filter(id => id !== assetId)
        : [...prev, assetId]
    );
  };

  const updateNotes = (assetId, notes) => {
    setPortfolioData(prev => ({
      ...prev,
      assets: prev.assets.map(asset => 
        asset.id === assetId ? { ...asset, notes } : asset
      )
    }));
  };

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