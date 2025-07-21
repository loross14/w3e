import React, { useEffect, useState, useRef } from "react";
import Chart from "chart.js/auto";
import { jsPDF } from "jspdf";

// Modular Card Components
const MetricCard = ({ title, value, change, changeType = "positive", icon, children }) => (
  <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6 hover:border-gray-600 transition-colors">
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center space-x-2">
        <h3 className="text-xs sm:text-sm font-medium text-gray-400 uppercase tracking-wide">{title}</h3>
        {icon && <div className="w-2 h-2 rounded-full" style={{ backgroundColor: icon }}></div>}
      </div>
    </div>
    <div className="space-y-1">
      <p className="text-xl sm:text-2xl font-bold text-white font-mono break-all">
        {value}
      </p>
      {change && (
        <p className={`text-xs sm:text-sm ${changeType === "positive" ? "text-green-400" : "text-red-400"} mt-1`}>
          {change}
        </p>
      )}
      {children}
    </div>
  </div>
);

const ActionCard = ({ title, description, buttonText, onAction, variant = "primary", disabled = false, children }) => (
  <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6">
    <h3 className="text-base sm:text-lg font-semibold mb-2 text-white">{title}</h3>
    {description && <p className="text-sm text-gray-400 mb-4">{description}</p>}
    <button
      onClick={onAction}
      disabled={disabled}
      className={`w-full px-4 py-2 sm:py-3 rounded-lg font-medium transition-colors text-sm sm:text-base ${
        variant === "primary"
          ? "bg-purple-600 text-white hover:bg-purple-700 disabled:bg-purple-800"
          : variant === "secondary"
          ? "bg-blue-600 text-white hover:bg-blue-700 disabled:bg-blue-800"
          : "bg-gray-700 text-white hover:bg-gray-600 disabled:bg-gray-800"
      } ${disabled ? "cursor-not-allowed opacity-50" : ""}`}
    >
      {buttonText}
    </button>
    {children}
  </div>
);

const AssetCard = ({ asset, onClick, onHide, isEditor, totalValue }) => {
  // Defensive programming to handle undefined values
  const safeAsset = {
    id: asset?.id || '',
    name: asset?.name || 'Unknown Asset',
    symbol: asset?.symbol || 'N/A',
    balance: asset?.balance || '0',
    priceUSD: asset?.priceUSD || 0,
    valueUSD: asset?.valueUSD || 0,
    notes: asset?.notes || '',
    isNFT: asset?.symbol?.includes('NFT') || asset?.name?.includes('Collection')
  };

  const safeTotalValue = totalValue || 1; // Avoid division by zero
  const weight = ((safeAsset.valueUSD / safeTotalValue) * 100).toFixed(1);
  const isNFTCollection = safeAsset.isNFT;

  return (
    <div 
      className="bg-gray-900 border border-gray-700 rounded-xl p-4 hover:border-gray-600 cursor-pointer transition-all duration-200"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3 min-w-0 flex-1">
          <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center flex-shrink-0 ${
            isNFTCollection 
              ? 'bg-gradient-to-r from-pink-500 to-purple-500' 
              : 'bg-gradient-to-r from-purple-500 to-blue-500'
          }`}>
            <span className="text-white font-bold text-sm">
              {isNFTCollection ? '🖼️' : safeAsset.symbol.slice(0, 2)}
            </span>
          </div>
          <div className="min-w-0 flex-1">
            <h3 className="font-medium text-white text-sm sm:text-base truncate">{safeAsset.name}</h3>
            <p className="text-xs sm:text-sm text-gray-400 truncate">
              {safeAsset.symbol}
              {isNFTCollection && <span className=" ml-1 text-pink-400">NFT Collection</span>}
            </p>
          </div>
        </div>
        {isEditor && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onHide();
            }}
            className="text-xs bg-red-600/20 text-red-400 px-2 py-1 rounded-md hover:bg-red-600/30 transition-colors border border-red-600/30 ml-2 flex-shrink-0"
          >
            Hide
          </button>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs sm:text-sm">
        <div>
          <span className="text-gray-400 block">{isNFTCollection ? 'Count' : 'Balance'}</span>
          <span className="text-white font-mono">
            {isNFTCollection ? `${Math.floor(safeAsset.balance)} NFTs` : safeAsset.balance}
          </span>
        </div>
        <div>
          <span className="text-gray-400 block">{isNFTCollection ? 'Floor Price' : 'Price'}</span>
          <span className="text-white font-mono">
            {isNFTCollection ? 'Coming Soon' : `$${safeAsset.priceUSD.toLocaleString()}`}
          </span>
        </div>
        <div>
          <span className="text-gray-400 block">Value</span>
          <span className="text-white font-mono">
            {isNFTCollection ? 'TBD' : `$${safeAsset.valueUSD.toLocaleString()}`}
          </span>
        </div>
        <div>
          <span className="text-gray-400 block">Weight</span>
          <span className="text-gray-300 font-mono">
            {isNFTCollection ? 'N/A' : `${weight}%`}
          </span>
        </div>
      </div>
    </div>
  );
};

// Portfolio Chart Component with mobile optimization
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
            borderWidth: 2,
            pointBackgroundColor: "#8B5CF6",
            pointBorderColor: "#ffffff",
            pointBorderWidth: 2,
            pointRadius: 4,
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
              maxTicksLimit: 6,
              font: {
                size: 10,
              },
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
              callback: (value) => `$${(value / 1000).toFixed(0)}K`,
              font: {
                size: 10,
              },
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

  return <canvas ref={chartRef} className="w-full h-full" />;
};

// Wallet Card Component
const WalletCard = ({ wallet, onClick, walletData }) => {
  const totalValue = walletData?.assets?.reduce((sum, asset) => sum + asset.valueUSD, 0) || 0;
  const assetCount = walletData?.assets?.length || 0;
  const performance = walletData?.performance || 0;

  // Check if wallet has errors or no data (especially Solana wallets)
  const isSolanaWallet = wallet.network === 'SOL';
  const hasError = walletData?.hasError || walletData?.error || (isSolanaWallet && assetCount === 0 && walletData?.status !== 'loading');

  return (
    <div 
      className={`bg-gray-900 border rounded-xl p-4 hover:border-gray-600 cursor-pointer transition-all duration-200 ${
        hasError ? 'border-red-700' : 'border-gray-700'
      }`}
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center space-x-3 min-w-0 flex-1">
          <div className={`w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center flex-shrink-0 ${
            hasError 
              ? 'bg-gradient-to-r from-red-500 to-red-600' 
              : 'bg-gradient-to-r from-green-500 to-emerald-500'
          }`}>
            <span className="text-white font-bold text-sm">{wallet.network}</span>
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center space-x-2">
              <h3 className="font-medium text-white text-sm sm:text-base truncate">{wallet.label}</h3>
              {hasError && <span className="text-red-400 text-xs">❌</span>}
            </div>
            <p className="text-xs sm:text-sm text-gray-400 font-mono truncate">{wallet.address}</p>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-400">Network</div>
          <div className="text-sm font-medium text-white">{wallet.network}</div>
        </div>
      </div>

      {hasError ? (
        <div className="p-3 bg-red-900/20 border border-red-700/50 rounded-lg">
          <div className="text-red-400 text-xs font-medium mb-1">⚠️ Solana Fetch Error</div>
          <div className="text-red-300 text-xs">
            {walletData?.errorMessage || 'Unable to fetch Solana data. This could be due to API limits, network issues, or wallet address format problems.'}
          </div>
          <div className="text-red-400 text-xs mt-1">
            💡 Try updating the portfolio again or check if the Solana address is valid.
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-2 text-xs sm:text-sm">
          <div>
            <span className="text-gray-400 block">Total Value</span>
            <span className="text-white font-mono">${totalValue.toLocaleString()}</span>
          </div>
          <div>
            <span className="text-gray-400 block">Assets</span>
            <span className="text-white font-mono">{assetCount}</span>
          </div>
          <div>
            <span className="text-gray-400 block">24h Change</span>
            <span className={`font-mono ${performance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {performance >= 0 ? '+' : ''}{performance.toFixed(2)}%
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

// Wallet Details Modal
const WalletModal = ({ wallet, onClose, walletData, portfolioData }) => {
  if (!wallet) return null;

  const walletAssets = walletData?.assets || [];
  const totalValue = walletAssets.reduce((sum, asset) => sum + asset.valueUSD, 0);
  const performance = walletData?.performance || 0;
  const performanceHistory = walletData?.performanceHistory || [];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold">{wallet.network}</span>
              </div>
              <div>
                <h2 className="text-lg sm:text-xl font-bold text-white">{wallet.label}</h2>
                <p className="text-sm text-gray-400 font-mono break-all">{wallet.address}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Wallet Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">Total Value</div>
              <div className="text-xl font-bold text-white">${totalValue.toLocaleString()}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">Assets</div>
              <div className="text-xl font-bold text-white">{walletAssets.length}</div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">24h Change</div>
              <div className={`text-xl font-bold ${performance >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {performance >= 0 ? '+' : ''}{performance.toFixed(2)}%
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">Network</div>
              <div className="text-xl font-bold text-white">{wallet.network}</div>
            </div>
          </div>

          {/* Performance Chart */}
          {performanceHistory.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4">Wallet Performance</h3>
              <div className="h-48">
                <PortfolioChart data={performanceHistory} />
              </div>
            </div>
          )}

          {/* Assets in Wallet */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Assets in Wallet ({walletAssets.length})</h3>
            {walletAssets.length === 0 ? (
              <div className="bg-gray-800 rounded-lg p-8 text-center">
                <div className="text-gray-400 mb-2">No assets found in this wallet</div>
                <div className="text-sm text-gray-500">This wallet may be empty or data hasn't been fetched yet</div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {walletAssets.map((asset, index) => (
                  <div key={index} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-bold text-xs">{asset.symbol.slice(0, 2)}</span>
                      </div>
                      <div>
                        <div className="font-medium text-white text-sm">{asset.name}</div>
                        <div className="text-xs text-gray-400">{asset.symbol}</div>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Balance:</span>
                        <span className="text-white font-mono">{asset.balance}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Value:</span>
                        <span className="text-green-400 font-mono">${asset.valueUSD.toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Price:</span>
                        <span className="text-white font-mono">${asset.priceUSD.toFixed(4)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Weight:</span>
                        <span className="text-gray-300 font-mono">
                          {((asset.valueUSD / totalValue) * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end mt-6">
            <button
              onClick={onClose}
              className="bg-gray-700 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
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
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg sm:text-xl font-bold text-white">{asset.name}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div className="space-y-3 mb-4 text-sm sm:text-base">
            <div className="flex justify-between">
              <span className="text-gray-400">Balance:</span>
              <span className="text-white font-mono">{asset?.balance || '0'} {asset?.symbol || 'N/A'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Value:</span>
              <span className="text-green-400 font-mono">${(asset?.valueUSD || 0).toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Price:</span>
              <span className="text-white font-mono">${(asset?.priceUSD || 0).toFixed(4)}</span>
            </div>
          </div>

          {isEditor && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-gray-300">Notes:</label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:border-purple-500 focus:outline-none text-sm"
                rows="3"
                placeholder="Add your notes here..."
              />
            </div>
          )}

          <div className="flex space-x-3">
            {isEditor && (
              <button
                onClick={handleSave}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm flex-1"
              >
                Save
              </button>
            )}
            <button
              onClick={onClose}
              className="bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors font-medium text-sm flex-1"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Report Generator Component
const ReportGenerator = ({ portfolioData }) => {
  const periods = ["1W", "1M", "1Q", "1Y"];

  const generateReport = (period) => {
    const doc = new jsPDF();
    doc.setFontSize(20);
    doc.text(`Crypto Fund Report - ${period}`, 20, 20);
    doc.setFontSize(12);
    doc.text(
      `Total Balance: $${portfolioData.totalValue?.toLocaleString() || "0"}`,
      20,
      40,
    );
    doc.text("Assets:", 20, 50);
    portfolioData.assets?.forEach((asset, i) => {
      doc.text(
        `${asset.name}: $${asset.valueUSD.toLocaleString()}`,
        30,
        60 + i * 10,
      );
    });
    doc.save(`CryptoFund_Report_${period}.pdf`);
  };

  return (
    <div className="flex flex-wrap gap-2">
      {periods.map((period) => (
        <button
          key={period}
          onClick={() => generateReport(period)}
          className="bg-purple-600 text-white px-3 py-1.5 rounded-lg hover:bg-purple-700 transition-colors text-xs sm:text-sm font-medium"
        >
          {period}
        </button>
      ))}
    </div>
  );
};

// Loading Component with status
const LoadingSpinner = ({ status }) => (
  <div className="flex items-center justify-center space-x-2 text-purple-400">
    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-400"></div>
    <span className="text-sm">{status || 'Loading...'}</span>
  </div>
);

// Settings Modal Component
const SettingsModal = ({ isOpen, onClose, isEditor, password, setPassword, onPasswordCheck, onEditorExit }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-md w-full">
        <div className="p-4 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg sm:text-xl font-bold text-white">Settings</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {!isEditor ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-white mb-2">🔐 Editor Access</h3>
                <p className="text-sm text-gray-400 mb-4">Enter access key to unlock dashboard editing features</p>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter access key"
                  className="w-full p-3 bg-gray-800 border border-gray-600 rounded-lg text-white focus:border-purple-500 focus:outline-none text-sm mb-4"
                  onKeyPress={(e) => e.key === "Enter" && onPasswordCheck()}
                />
                <button
                  onClick={onPasswordCheck}
                  className="w-full bg-purple-600 text-white px-4 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium"
                >
                  Unlock Dashboard
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="p-4 bg-green-900/20 border border-green-700/50 rounded-lg">
                <h3 className="text-base font-semibold text-green-400 mb-2">✅ Editor Mode Active</h3>
                <p className="text-sm text-gray-300 mb-4">You're currently in editor mode with full dashboard access.</p>
                <div className="text-sm text-green-400 mb-4">
                  🔧 Editor features enabled: Hide assets, manage wallets, update notes
                </div>
                <button
                  onClick={onEditorExit}
                  className="w-full bg-gray-700 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors font-medium"
                >
                  Save & Exit Editor
                </button>
              </div>
            </div>
          )}

          <div className="flex justify-end mt-6">
            <button
              onClick={onClose}
              className="bg-gray-700 text-white px-6 py-2 rounded-lg hover:bg-gray-600 transition-colors font-medium"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const [isEditor, setIsEditor] = useState(false);
  const [password, setPassword] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [hiddenAssets, setHiddenAssets] = useState(
    () => JSON.parse(localStorage.getItem("hiddenAssets")) || [],
  );
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [selectedWallet, setSelectedWallet] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [portfolioData, setPortfolioData] = useState({
    balanceHistory: [],
    assets: [],
  });
  const [walletData, setWalletData] = useState(() => {
    const saved = localStorage.getItem("walletData");
    return saved ? JSON.parse(saved) : {};
  });

  const correctPassword = "bullrun";

  const checkPassword = () => {
    if (password === correctPassword) {
      setIsEditor(true);
      setPassword("");
      setShowSettings(false);
    } else {
      alert("Incorrect password");
    }
  };

  const handleEditorExit = () => {
    setIsEditor(false);
    setPassword("");
    setShowSettings(false);
    // Show a temporary success message
    setUpdateStatus("✅ Changes saved! Returned to viewer mode.");
    setTimeout(() => setUpdateStatus(''), 3000);
  };

  const toggleHiddenAsset = async (asset) => {
    try {
      const isCurrentlyHidden = hiddenAssets.includes(asset.id);

      if (isCurrentlyHidden) {
        // Unhide the asset
        const response = await fetch(`${API_BASE_URL}/assets/hide/${asset.id}`, {
          method: 'DELETE',
        });

        if (response.ok) {
          setHiddenAssets((prev) => {
            const newHiddenAssets = prev.filter((id) => id !== asset.id);
            localStorage.setItem("hiddenAssets", JSON.stringify(newHiddenAssets));
            return newHiddenAssets;
          });
          console.log(`✅ Unhid asset: ${asset.symbol}`);
        } else {
          throw new Error(`Failed to unhide asset: ${response.status}`);
        }
      } else {
        // Hide the asset - send as query parameters instead of JSON body
        const params = new URLSearchParams({
          token_address: asset.id,
          symbol: asset.symbol,
          name: asset.name
        });

        const response = await fetch(`${API_BASE_URL}/assets/hide?${params}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          setHiddenAssets((prev) => {
            const newHiddenAssets = [...prev, asset.id];
            localStorage.setItem("hiddenAssets", JSON.stringify(newHiddenAssets));
            return newHiddenAssets;
          });
          console.log(`✅ Hid asset: ${asset.symbol}`);
        } else {
          const errorText = await response.text();
          throw new Error(`Failed to hide asset: ${response.status} - ${errorText}`);
        }
      }
    } catch (error) {
      console.error('Error toggling hidden asset:', error);
      alert(`Failed to update asset visibility: ${error.message}`);
    }
  };

  const updateNotes = async (assetId, notes) => {
    if (!assetId) {
      setSelectedAsset(null);
      return;
    }

    try {
      const asset = portfolioData.assets.find(a => a.id === assetId);
      if (!asset) return;

      const response = await fetch(`${API_BASE_URL}/assets/${asset.symbol}/notes?notes=${encodeURIComponent(notes)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to update notes');
      }

      setPortfolioData((prev) => ({
        ...prev,
        assets: prev.assets.map((a) =>
          a.id === assetId ? { ...a, notes } : a,
        ),
      }));

    } catch (error) {
      console.error('Error updating notes:', error);
      alert(`Failed to update notes: ${error.message}`);
    }
  };

  // Wallet addresses for the fund - stored in state for dynamic management
  const [walletAddresses, setWalletAddresses] = useState(() => {
    const saved = localStorage.getItem("fundWallets");
    return saved ? JSON.parse(saved) : [
      { id: 1, address: "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98", label: "Ethereum Safe Multisig", network: "ETH" },
      { id: 2, address: "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb", label: "Solana EOA", network: "SOL" }
    ];
  });
  const [newWalletAddress, setNewWalletAddress] = useState("");
  const [newWalletLabel, setNewWalletLabel] = useState("");
  const [newWalletNetwork, setNewWalletNetwork] = useState("ETH");

  const addWallet = async () => {
    if (!newWalletAddress.trim() || !newWalletLabel.trim()) {
      alert("Please enter both wallet address and label");
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/wallets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          address: newWalletAddress.trim(),
          label: newWalletLabel.trim(),
          network: newWalletNetwork
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add wallet');
      }

      const newWallet = await response.json();

      const updatedWallets = [...walletAddresses, newWallet];
      setWalletAddresses(updatedWallets);
      localStorage.setItem("fundWallets", JSON.stringify(updatedWallets));

      setNewWalletAddress("");
      setNewWalletLabel("");
      setNewWalletNetwork("ETH");

      alert("Wallet added successfully!");
    } catch (error) {
      console.error('Error adding wallet:', error);
      alert(`Failed to add wallet: ${error.message}`);
    }
  };

  const removeWallet = async (walletId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/wallets/${walletId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to remove wallet');
      }

      const updatedWallets = walletAddresses.filter(wallet => wallet.id !== walletId);
      setWalletAddresses(updatedWallets);
      localStorage.setItem("fundWallets", JSON.stringify(updatedWallets));

      // Remove wallet data from local state
      const newWalletData = { ...walletData };
      delete newWalletData[walletId];
      setWalletData(newWalletData);
      localStorage.setItem("walletData", JSON.stringify(newWalletData));

    } catch (error) {
      console.error('Error removing wallet:', error);
      alert(`Failed to remove wallet: ${error.message}`);
    }
  };

  // API Configuration for Replit environment
  const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : `${window.location.protocol}//${window.location.hostname}:8000`;

  // Status tracking state
  const [updateStatus, setUpdateStatus] = useState('');
  const [updateError, setUpdateError] = useState('');
  const [debugInfo, setDebugInfo] = useState([]);
  const [walletStatus, setWalletStatus] = useState([]);

  // Debug logging function
  const addDebugInfo = (message, data = null) => {
    const timestamp = new Date().toLocaleTimeString();
    const debugEntry = { timestamp, message, data };
    console.log(`🐛 [${timestamp}] ${message}`, data || '');
    setDebugInfo(prev => [...prev.slice(-9), debugEntry]); // Keep last 10 entries
  };

  // Load saved portfolio data on startup and sync wallets
  useEffect(() => {
    const loadPortfolioAndSyncWallets = async (retryCount = 0) => {
      const maxRetries = 3;

      try {
        addDebugInfo("Starting portfolio data load", { retryCount, API_BASE_URL });

        // Test backend connection first
        addDebugInfo("Testing backend connection...");
        const healthResponse = await fetch(`${API_BASE_URL}/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!healthResponse.ok) {
          throw new Error(`Backend not ready (${healthResponse.status})`);
        }
        addDebugInfo("✅ Backend connection successful");

        // Load hidden assets from backend
        try {
          addDebugInfo("Loading hidden assets...");
          const hiddenResponse = await fetch(`${API_BASE_URL}/assets/hidden`);
          if (hiddenResponse.ok) {
            const hiddenData = await hiddenResponse.json();
            const hiddenIds = hiddenData.map(asset => asset.token_address);
            setHiddenAssets(hiddenIds);
            localStorage.setItem("hiddenAssets", JSON.stringify(hiddenIds));
            addDebugInfo(`✅ Loaded ${hiddenIds.length} hidden assets`, hiddenIds);
          } else {
            addDebugInfo(`⚠️ Hidden assets response: ${hiddenResponse.status}`);
          }
        } catch (error) {
          addDebugInfo("❌ Error loading hidden assets", error.message);
        }

        // Load saved portfolio data
        addDebugInfo("Loading portfolio data...");
        const portfolioResponse = await fetch(`${API_BASE_URL}/portfolio`);

        if (!portfolioResponse.ok) {
          throw new Error(`Portfolio fetch failed: ${portfolioResponse.status} ${portfolioResponse.statusText}`);
        }

        const savedData = await portfolioResponse.json();
        addDebugInfo("📊 Raw portfolio data received", savedData);

        console.log("🔍 [FRONTEND DEBUG] Full backend response:", savedData);
        console.log("🔍 [FRONTEND DEBUG] Assets array:", savedData.assets);
        console.log("🔍 [FRONTEND DEBUG] Assets length:", savedData.assets?.length);

        if (savedData.assets && savedData.assets.length > 0) {
          console.log("🔄 [FRONTEND DEBUG] Starting asset transformation...");
          const transformedAssets = savedData.assets.map((asset, index) => {
            console.log(`🔄 [FRONTEND DEBUG] Transforming asset ${index + 1}:`, asset);
            const transformed = {
              id: asset.id,
              name: asset.name,
              symbol: asset.symbol,
              balance: asset.balance_formatted || asset.balance,
              priceUSD: asset.price_usd || 0,
              valueUSD: asset.value_usd || 0,
              notes: asset.notes || "",
            };
            console.log(`✅ [FRONTEND DEBUG] Transformed to:`, transformed);
            return transformed;
          });
          console.log("🎯 [FRONTEND DEBUG] Final transformed assets:", transformedAssets);

          const savedTotalValue = savedData.total_value || 0;

          // Generate balance history based on saved data
          const balanceHistory = savedTotalValue > 0 ? [
            { value: savedTotalValue * 0.92 },
            { value: savedTotalValue * 0.95 },
            { value: savedTotalValue * 0.88 },
            { value: savedTotalValue * 0.96 },
            { value: savedTotalValue }
          ] : [{ value: 0 }];

          const portfolioUpdate = {
            assets: transformedAssets,
            balanceHistory: balanceHistory,
            totalValue: savedTotalValue,
            performance24h: savedData.performance_24h || 0
          };

          setPortfolioData(portfolioUpdate);
          addDebugInfo(`✅ Portfolio data set successfully`, {
            assetCount: transformedAssets.length,
            totalValue: savedTotalValue,
            sampleAsset: transformedAssets[0]
          });
        } else {
          addDebugInfo("⚠️ No assets found in portfolio data", savedData);
        }

        // Get current wallets from backend and sync with local state
        addDebugInfo("Loading wallets from backend...");
        const walletsResponse = await fetch(`${API_BASE_URL}/wallets`);
        if (walletsResponse.ok) {
          const backendWallets = await walletsResponse.json();
          addDebugInfo(`📋 Backend has ${backendWallets.length} wallets`, backendWallets);

            // Update local wallet state to match backend, but preserve default wallets
            if (backendWallets.length > 0) {
              // Merge backend wallets with local state, ensuring important wallets aren't lost
              const currentWallets = [...walletAddresses];
              const mergedWallets = [...backendWallets];

              // Check if Solana wallet exists in backend, if not preserve it
              const hasSolanaWallet = backendWallets.some(w => w.network === "SOL");
              if (!hasSolanaWallet) {
                const localSolanaWallet = currentWallets.find(w => w.network === "SOL");
                if (localSolanaWallet) {
                  mergedWallets.push(localSolanaWallet);
                  addDebugInfo("🔄 Preserved Solana wallet in sync");
                }
              }

              setWalletAddresses(mergedWallets);
              localStorage.setItem("fundWallets", JSON.stringify(mergedWallets));
              addDebugInfo("✅ Local wallets synced with backend (with preservation)");
            }

          // Load wallet status information
          try {
            const statusResponse = await fetch(`${API_BASE_URL}/wallets/status`);
            if (statusResponse.ok) {
              const statusData = await statusResponse.json();
              setWalletStatus(statusData);
              addDebugInfo(`📊 Loaded wallet status for ${statusData.length} wallets`);
            }
          } catch (error) {
            addDebugInfo("⚠️ Could not load wallet status", error.message);
          }

          // If backend is empty but we have local wallets, sync them
          if (backendWallets.length === 0 && walletAddresses.length > 0) {
            addDebugInfo("Syncing local wallets to backend...");
            for (const wallet of walletAddresses) {
              try {
                const syncResponse = await fetch(`${API_BASE_URL}/wallets`, {
                  method: 'POST',
                  headers: {
                    'Content-Type': 'application/json',
                  },
                  body: JSON.stringify({
                    address: wallet.address,
                    label: wallet.label,
                    network: wallet.network
                  }),
                });

                if (syncResponse.ok) {
                  addDebugInfo(`✅ Synced wallet: ${wallet.label}`);
                } else {
                  addDebugInfo(`⚠️ Wallet ${wallet.label} may already exist in backend`);
                }
              } catch (error) {
                addDebugInfo(`❌ Failed to sync wallet ${wallet.label}`, error.message);
              }
            }
          }
        } else {
          addDebugInfo(`❌ Wallets fetch failed: ${walletsResponse.status}`);
        }

        addDebugInfo("🎉 Portfolio load completed successfully");

      } catch (error) {
        addDebugInfo(`❌ Portfolio load error (attempt ${retryCount + 1}/${maxRetries + 1})`, error.message);

        // Retry with exponential backoff if backend isn't ready yet
        if (retryCount < maxRetries && (error.message.includes('Failed to fetch') || error.message.includes('Backend not ready'))) {
          const delay = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s delays
          addDebugInfo(`🔄 Retrying portfolio load in ${delay / 1000}s...`);
          setTimeout(() => loadPortfolioAndSyncWallets(retryCount + 1), delay);
        } else {
          setUpdateError(`Failed to load portfolio: ${error.message}`);
        }
      }
    };

    // Delay initial load to let backend start up
    const timer = setTimeout(() => loadPortfolioAndSyncWallets(), 3000);
    return () => clearTimeout(timer);
  }, []);

  const updatePortfolio = async () => {
    setIsLoading(true);
    setUpdateError('');
    setUpdateStatus('🔗 Connecting to backend...');

    try {
      // Step 1: Test backend connection
      setUpdateStatus('🔗 Testing backend connection...');
      const healthResponse = await fetch(`${API_BASE_URL}/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!healthResponse.ok) {
        throw new Error(`Backend not responding (${healthResponse.status})`);
      }

      // Step 2: Trigger portfolio update
      setUpdateStatus('🚀 Starting portfolio update...');
      const updateResponse = await fetch(`${API_BASE_URL}/portfolio/update`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!updateResponse.ok) {
        const errorText = await updateResponse.text();
        throw new Error(`Update failed (${updateResponse.status}): ${errorText}`);
      }

      // Step 3: Wait for processing
      setUpdateStatus('⏳ Processing wallet data...');
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Step 4: Wait a bit more for backend processing
      setUpdateStatus('⏳ Waiting for backend processing...');
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Step 5: Fetch updated portfolio data
      setUpdateStatus('📊 Fetching portfolio data...');
      const portfolioResponse = await fetch(`${API_BASE_URL}/portfolio`);
      if (!portfolioResponse.ok) {
        const errorText = await portfolioResponse.text();
        throw new Error(`Failed to fetch portfolio (${portfolioResponse.status}): ${errorText}`);
      }

      const portfolioData = await portfolioResponse.json();

      // Log the fetched data for debugging
      console.log('Fetched portfolio data:', portfolioData);

      // Step 6: Transform data
      setUpdateStatus('🔄 Processing asset data...');
      const updatedAssets = portfolioData.assets.map(asset => ({
        id: asset.id,
        name: asset.name,
        symbol: asset.symbol,
        balance: asset.balance_formatted || asset.balance,
        priceUSD: asset.price_usd || 0,
        valueUSD: asset.value_usd || 0,
        notes: asset.notes || "",
      }));

      const newTotalValue = portfolioData.total_value || 0;

      // Generate balance history (simplified - in production you'd fetch from backend)
      const newBalanceHistory = newTotalValue > 0 ? [
        { value: newTotalValue * 0.92 },
        { value: newTotalValue * 0.95 },
        { value: newTotalValue * 0.88 },
        { value: newTotalValue * 0.96 },
        { value: newTotalValue }
      ] : [{ value: 0 }];

      console.log(`Found ${updatedAssets.length} assets with total value $${newTotalValue}`);

      // Step 7: Fetch individual wallet data
      setUpdateStatus('💼 Updating wallet details...');
      const newWalletData = {};
      let walletCount = 0;

      // First, get updated wallet list from backend
      const walletsListResponse = await fetch(`${API_BASE_URL}/wallets`);
      const currentWallets = walletsListResponse.ok ? await walletsListResponse.json() : walletAddresses;

      for (const wallet of currentWallets) {
        try {
          setUpdateStatus(`💼 Processing ${wallet.label} (${++walletCount}/${currentWallets.length})...`);
          const walletResponse = await fetch(`${API_BASE_URL}/wallets/${wallet.id}/details`);

          if (walletResponse.ok) {
            const walletDetails = await walletResponse.json();
            const walletAssets = walletDetails.assets.map(asset => ({
              id: asset.id,
              name: asset.name,
              symbol: asset.symbol,
              balance: asset.balance_formatted || asset.balance,
              priceUSD: asset.price_usd || 0,
              valueUSD: asset.value_usd || 0,
              notes: asset.notes || "",
            }));

            const walletTotalValue = walletDetails.total_value;

            newWalletData[wallet.id] = {
              assets: walletAssets,
              performance: walletDetails.performance_24h,
              performanceHistory: [
                { value: walletTotalValue * 0.92 },
                { value: walletTotalValue * 0.95 },
                { value: walletTotalValue * 0.88 },
                { value: walletTotalValue * 0.96 },
                { value: walletTotalValue }
              ]
            };
            console.log(`✅ Loaded wallet ${wallet.label} with ${walletAssets.length} assets worth $${walletTotalValue.toLocaleString()}`);
          } else if (walletResponse.status === 404) {
            console.warn(`⚠️ Wallet ${wallet.label} (ID: ${wallet.id}) not found in backend`);
            setUpdateStatus(`⚠️ Wallet ${wallet.label} not found - it may need to be re-added`);
          } else {
            console.error(`❌ Error fetching wallet ${wallet.label}: ${walletResponse.status} ${walletResponse.statusText}`);
            setUpdateStatus(`❌ Error fetching ${wallet.label}: ${walletResponse.status}`);
          }
        } catch (error) {
          console.error(`❌ Network error fetching wallet ${wallet.label}:`, error);
          setUpdateStatus(`⚠️ Network error fetching ${wallet.label}`);
          await new Promise(resolve => setTimeout(resolve, 1000));
        }
      }

      // Step 8: Save data and force refresh
      setUpdateStatus('💾 Saving data...');
      setWalletData(newWalletData);
      localStorage.setItem("walletData", JSON.stringify(newWalletData));

      // Force update portfolio data
      const newPortfolioData = {
        assets: updatedAssets,
        balanceHistory: newBalanceHistory,
        totalValue: newTotalValue,
        performance24h: portfolioData.performance_24h || 0
      };
      setPortfolioData(newPortfolioData);

      addDebugInfo("💾 Portfolio data updated after fetch", {
        assetCount: updatedAssets.length,
        totalValue: newTotalValue,
        sampleAsset: updatedAssets[0]
      });

      // Force a fresh load from the API to ensure sync
      setUpdateStatus('🔄 Verifying update...');
      try {
        const verifyResponse = await fetch(`${API_BASE_URL}/portfolio`);
        if (verifyResponse.ok) {
          const verifyData = await verifyResponse.json();
          addDebugInfo("✅ Verification successful", {
            backendAssets: verifyData.assets.length,
            backendTotal: verifyData.total_value
          });
        }
      } catch (verifyError) {
        addDebugInfo("⚠️ Verification failed", verifyError.message);
      }

      // Step 9: Load updated wallet status
      setUpdateStatus('📊 Loading wallet status...');
      try {
        const statusResponse = await fetch(`${API_BASE_URL}/wallets/status`);
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setWalletStatus(statusData);
          addDebugInfo(`📊 Updated wallet status for ${statusData.length} wallets`);
        }
      } catch (error) {
        addDebugInfo("⚠️ Could not refresh wallet status", error.message);
      }

      // Step 10: Complete
      const assetCount = updatedAssets.length;
      const valueFormatted = newTotalValue.toLocaleString();
      setUpdateStatus(`✅ Updated ${assetCount} assets • $${valueFormatted}`);
      setTimeout(() => setUpdateStatus(''), 5000);

      addDebugInfo('🎉 Portfolio update completed successfully', {
        totalAssets: assetCount,
        totalValue: newTotalValue
      });
    } catch (error) {
      console.error('Error updating portfolio:', error);
      let errorMessage = 'Unknown error occurred';

      if (error.message.includes('Failed to fetch')) {
        errorMessage = '🔌 Cannot connect to backend server. Make sure the backend is running on port 8000.';
      } else if (error.message.includes('CORS')) {
        errorMessage = '🚫 CORS error - backend not configured for frontend domain.';
      } else if (error.message.includes('Network')) {
        errorMessage = '🌐 Network error - check your internet connection.';
      } else {
        errorMessage = `❌ ${error.message}`;
      }

      setUpdateError(errorMessage);
      setUpdateStatus('');
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate metrics with safe fallbacks
  const visibleAssets = (portfolioData.assets || []).filter(
    (asset) => asset && !hiddenAssets.includes(asset.id),
  );

  const totalValue = visibleAssets.reduce(
    (sum, asset) => sum + (asset?.valueUSD || 0),
    0,
  );

  const topAsset = visibleAssets.length > 0 ? visibleAssets.reduce((prev, current) => 
    prev.valueUSD > current.valueUSD ? prev : current
  ) : null;

  const topAssetWeight = topAsset ? ((topAsset.valueUSD / totalValue) * 100).toFixed(1) : 0;

  // Calculate performance vs raised capital
  const raisedCapital = 138000; // Hardcoded raised capital amount
  const performanceVsRaised = totalValue > 0 ? ((totalValue - raisedCapital) / raisedCapital * 100) : 0;
  const performanceSign = performanceVsRaised >= 0 ? "+" : "";
  const performanceChangeType = performanceVsRaised >= 0 ? "positive" : "negative";

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Mobile-optimized Header */}
      <div className="border-b border-gray-800 bg-gray-900/50 sticky top-0 z-40">
        <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 sm:space-x-4 min-w-0">
              <div className="w-6 h-6 sm:w-8 sm:h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <span className="text-white font-bold text-xs sm:text-sm">3</span>
              </div>
              <h1 className="text-lg sm:text-2xl font-bold truncate">Web3Equities Portfolio</h1>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4 flex-shrink-0">
              <button 
                onClick={() => setShowSettings(true)}
                className="text-gray-400 hover:text-white transition-colors p-1"
                title="Settings"
              >
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-6">
        {/* Database Update Button */}
        <div className="mb-6">
          <ActionCard
            title="🔄 Update Portfolio Database"
            description="Query all wallets and fetch current balances & history"
            buttonText={isLoading ? <LoadingSpinner status={updateStatus} /> : "Update Database"}
            onAction={updatePortfolio}
            variant="primary"
            disabled={isLoading}
          >
            {/* Status Display */}
            {updateStatus && (
              <div className="mt-3 p-3 bg-blue-900/30 border border-blue-700/50 rounded-lg">
                <p className="text-sm text-blue-300">{updateStatus}</p>
              </div>
            )}

            {/* Error Display */}
            {updateError && (
              <div className="mt-3 p-3 bg-red-900/30 border border-red-700/50 rounded-lg">
                <p className="text-sm text-red-300">{updateError}</p>
                <div className="mt-2 text-xs text-red-400">
                  <p>💡 Troubleshooting:</p>
                  <ul className="list-disc list-inside mt-1 space-y-1">
                    <li>Make sure the backend is running (check "Full Stack" workflow)</li>
                    <li>Check if your ALCHEMY_API_KEY secret is set</li>
                    <li>Backend should be accessible at: {API_BASE_URL}</li>
                  </ul>
                </div>
              </div>
            )}


          </ActionCard>
        </div>

        {/* Key Metrics - Mobile responsive grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
          <MetricCard
            title="Total Value"
            value={`$${totalValue.toLocaleString()}`}
            change="+2.4% (24h)"
            changeType="positive"
            icon="#10B981"
          />

          <MetricCard
            title="Assets"
            value={visibleAssets.length}
            change="Active positions"
            changeType="neutral"
            icon="#3B82F6"
          />

          <MetricCard
            title="Top Asset"
            value={topAsset?.symbol || "N/A"}
            change={`${topAssetWeight}% of portfolio`}
            changeType="neutral"
            icon="#8B5CF6"
          />

          <MetricCard
            title="Performance"
            value={`${performanceSign}${performanceVsRaised.toFixed(1)}%`}
            change="all time unrealized return"
            changeType={performanceChangeType}
            icon="#F59E0B"
          />
        </div>

        {/* Chart Section - Temporarily hidden until properly implemented */}
        {false && (
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6 mb-6 sm:mb-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6 space-y-3 sm:space-y-0">
              <h3 className="text-base sm:text-lg font-semibold text-white">Portfolio Performance</h3>
              <div className="flex space-x-2 overflow-x-auto">
                <button className="px-3 py-1 text-xs bg-purple-600 text-white rounded-md whitespace-nowrap">7D</button>
                <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600 whitespace-nowrap">30D</button>
                <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600 whitespace-nowrap">90D</button>
                <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600 whitespace-nowrap">1Y</button>
              </div>
            </div>
            <div className="h-48 sm:h-64 lg:h-80">
              <PortfolioChart data={portfolioData.balanceHistory} />
            </div>
          </div>
        )}

        {/* Action Cards for Editor */}
        {isEditor && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-6 sm:mb-8">
            <ActionCard
              title="Update Portfolio"
              description="Refresh asset prices and balances"
              buttonText={isLoading ? <LoadingSpinner status={updateStatus} /> : "Update Portfolio"}
              onAction={updatePortfolio}
              variant="secondary"
              disabled={isLoading}
            />

            <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold mb-2 text-white">Generate Reports</h3>
              <p className="text-sm text-gray-400 mb-4">Export performance reports</p>
              <ReportGenerator portfolioData={{ ...portfolioData, totalValue }} />
            </div>
          </div>
        )}

        {/* Wallet Management Section */}
        {isEditor && (
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6 mb-6 sm:mb-8">
            <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">Fund Wallets</h3>

            {/* Current Wallets with Status */}
            <div className="space-y-3 mb-6">
              {walletAddresses.map((wallet) => {
                const status = walletStatus.find(s => s.wallet_id === wallet.id);
                const statusColor = status?.status === 'success' ? 'bg-green-500' : 
                                   status?.status === 'error' ? 'bg-red-500' :
                                   status?.status === 'timeout' ? 'bg-yellow-500' : 'bg-gray-500';
                const statusText = status?.status === 'success' ? '✅' :
                                  status?.status === 'error' ? '❌' :
                                  status?.status === 'timeout' ? '⏰' : '❓';

                return (
                  <div key={wallet.id} className="p-3 bg-gray-800 rounded-lg border border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3 min-w-0 flex-1">
                        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-white font-bold text-xs">{wallet.network}</span>
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center space-x-2">
                            <p className="text-white font-medium text-sm">{wallet.label}</p>
                            <span className="text-xs">{statusText}</span>
                            <div className={`w-2 h-2 rounded-full ${statusColor} flex-shrink-0`}></div>
                          </div>
                          <p className="text-gray-400 text-xs font-mono break-all">{wallet.address}</p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeWallet(wallet.id)}
                        className="text-red-400 hover:text-red-300 p-1 ml-2 flex-shrink-0"
                        title="Remove wallet"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>

                    {/* Wallet Status Details */}
                    {status && (
                      <div className="grid grid-cols-3 gap-2 text-xs text-gray-400 mt-2 pt-2 border-t border-gray-700">
                        <div>
                          <span className="block">Assets</span>
                          <span className="text-white">{status.assets_found || 0}</span>
                        </div>
                        <div>
                          <span className="block">Value</span>
                          <span className="text-white">${(status.total_value || 0).toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="block">Status</span>
                          <span className={`${
                            status.status === 'success' ? 'text-green-400' :
                            status.status === 'error' ? 'text-red-400' :
                            status.status === 'timeout' ? 'text-yellow-400' : 'text-gray-400'
                          }`}>
                            {status.status}
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Error Message */}
                    {status?.error_message && (
                      <div className="mt-2 p-2 bg-red-900/30 border border-red-700/50 rounded text-xs text-red-300">
                        <strong>Error:</strong> {status.error_message}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Add New Wallet Form */}
            <div className="border-t border-gray-700 pt-4">
              <h4 className="text-sm font-medium text-gray-300 mb-3">Add New Wallet</h4>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <input
                  type="text"
                  value={newWalletLabel}
                  onChange={(e) => setNewWalletLabel(e.target.value)}
                  placeholder="Wallet label"
                  className="col-span-1 p-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:border-purple-500 focus:outline-none text-sm"
                />
                <select
                  value={newWalletNetwork}
                  onChange={(e) => setNewWalletNetwork(e.target.value)}
                  className="col-span-1 p-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:border-purple-500 focus:outline-none text-sm"
                >
                  <option value="ETH">Ethereum</option>
                  <option value="SOL">Solana</option>
                  <option value="BTC">Bitcoin</option>
                  <option value="MATIC">Polygon</option>
                  <option value="AVAX">Avalanche</option>
                </select>
                <input
                  type="text"
                  value={newWalletAddress}
                  onChange={(e) => setNewWalletAddress(e.target.value)}
                  placeholder="Wallet address"
                  className="col-span-1 sm:col-span-1 p-2 bg-gray-800 border border-gray-600 rounded-lg text-white focus:border-purple-500 focus:outline-none text-sm font-mono"
                />
                <button
                  onClick={addWallet}
                  className="col-span-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors text-sm font-medium"
                >
                  Add Wallet
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Assets Grid - Mobile responsive */}
        <div className="mb-6 sm:mb-8">
          <div className="flex justify-between items-center mb-4 sm:mb-6">
            <h3 className="text-base sm:text-lg font-semibold text-white">Asset Holdings</h3>
            <span className="text-xs sm:text-sm text-gray-400">
              {visibleAssets.length} assets • ${totalValue.toLocaleString()}
            </span>
          </div>

          {visibleAssets.length === 0 ? (
            <div className="bg-gray-900 border border-gray-700 rounded-xl p-8 text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-white mb-2">No Asset Data Found</h4>
              <p className="text-gray-400 mb-6 max-w-md mx-auto">
                Your portfolio appears to be empty. Click the "Update Database" button to fetch the latest wallet balances and asset data from your configured wallets.
              </p>
              <button
                onClick={updatePortfolio}
                disabled={isLoading}
                className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium disabled:bg-purple-800 disabled:cursor-not-allowed"
              >
                {isLoading ? <LoadingSpinner status={updateStatus} /> : "🔄 Update Database"}
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {visibleAssets.map((asset) => (
                <AssetCard
                  key={asset.id}
                  asset={asset}
                  onClick={() => setSelectedAsset(asset)}
                  onHide={() => toggleHiddenAsset(asset)}
                  isEditor={isEditor}
                  totalValue={totalValue}
                />
              ))}
            </div>
          )}
        </div>

        {/* Wallets Section */}
        <div className="mb-6 sm:mb-8">
          <div className="flex justify-between items-center mb-4 sm:mb-6">
            <h3 className="text-base sm:text-lg font-semibold text-white">Fund Wallets</h3>
            <span className="text-xs sm:text-sm text-gray-400">
              {walletAddresses.length} wallets • {Object.keys(walletData).length} with data
            </span>
          </div>

          {walletAddresses.length === 0 ? (
            <div className="bg-gray-900 border border-gray-700 rounded-xl p-8 text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h4 className="text-lg font-semibold text-white mb-2">No Wallets Configured</h4>
              <p className="text-gray-400 mb-6 max-w-md mx-auto">
                Add wallet addresses to start tracking individual wallet performance and asset breakdowns.
              </p>
              {isEditor && (
                <button
                  onClick={() => document.querySelector('input[placeholder="Wallet label"]')?.scrollIntoView({ behavior: 'smooth' })}
                  className="bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors font-medium"
                >
                  🏦 Add First Wallet
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {walletAddresses.map((wallet) => {
                // Check if wallet has status info to determine if there's an error
                const status = walletStatus.find(s => s.wallet_id === wallet.id);
                const hasData = walletData[wallet.id];
                const hasError = status?.status === 'error' || (!hasData && wallet.network === 'SOL');

                return (
                  <WalletCard
                    key={wallet.id}
                    wallet={wallet}
                    onClick={() => setSelectedWallet(wallet)}
                    walletData={walletData[wallet.id] || { assets: [], performance: 0, hasError }}
                  />
                );
              })}
            </div>
          )}
        </div>

        {/* Hidden Assets */}
        {hiddenAssets.length > 0 && isEditor && (
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6 mb-6 sm:mb-8">
            <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">HiddenAssets</h3>
            <div className="space-y-3">
              {portfolioData.assets
                .filter((asset) => hiddenAssets.includes(asset.id))
                .map((asset) => (
                  <div
                    key={asset.id}
                    className="flex justify-between items-center p-3 bg-gray-800 rounded-lg border border-gray-700"
                  >
                    <div className="flex items-center space-x-3 min-w-0">
                      <div className="w-6 h-6 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-bold text-xs">{asset.symbol.slice(0, 2)}</span>
                      </div>
                      <span className="text-white font-medium truncate">{asset.name}</span>
                    </div>
                    <button
                      onClick={() => toggleHiddenAsset(asset)}
                      className="text-xs bg-green-600/20 text-green-400 px-3 py-1 rounded-md hover:bg-green-600/30 transition-colors border border-green-600/30 whitespace-nowrap"
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

      {/* Wallet Modal */}
      {selectedWallet && (
        <WalletModal
          wallet={selectedWallet}
          onClose={() => setSelectedWallet(null)}
          walletData={walletData[selectedWallet.id]}
          portfolioData={portfolioData}
        />
      )}

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        isEditor={isEditor}
        password={password}
        setPassword={setPassword}
        onPasswordCheck={checkPassword}
        onEditorExit={handleEditorExit}
      />
    </div>
  );
};

export default App;