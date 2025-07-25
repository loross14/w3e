import React, { useEffect, useState, useRef } from "react";
import Chart from "chart.js/auto";
import { jsPDF } from "jspdf";

// Modular Card Components
const MetricCard = ({
  title,
  value,
  change,
  changeType = "positive",
  icon,
  children,
}) => (
  <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6 hover:border-gray-600 transition-colors">
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center space-x-2">
        <h3 className="text-xs sm:text-sm font-medium text-gray-400 uppercase tracking-wide">
          {title}
        </h3>
        {icon && (
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: icon }}
          ></div>
        )}
      </div>
    </div>
    <div className="space-y-1">
      <p className="text-xl sm:text-2xl font-bold text-white font-mono break-all">
        {value}
      </p>
      {change && (
        <div
          className={`text-xs sm:text-sm ${
            changeType === "positive"
              ? "text-green-400"
              : changeType === "negative"
                ? "text-red-400"
                : changeType === "white"
                  ? "text-white"
                  : "text-gray-400"
          } mt-1`}
        >
          {typeof change === "string" ? change : change}
        </div>
      )}
      {children}
    </div>
  </div>
);

const ActionCard = ({
  title,
  description,
  buttonText,
  onAction,
  variant = "primary",
  disabled = false,
  children,
}) => (
  <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6">
    <h3 className="text-base sm:text-lg font-semibold mb-2 text-white">
      {title}
    </h3>
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
    id: asset?.id || "",
    name: asset?.name || "Unknown Asset",
    symbol: asset?.symbol || "N/A",
    balance: asset?.balance || "0",
    priceUSD: asset?.priceUSD || 0,
    valueUSD: asset?.valueUSD || 0,
    purchase_price: asset?.purchase_price || 0,
    total_invested: asset?.total_invested || 0,
    unrealized_pnl: asset?.unrealized_pnl || 0,
    total_return_pct: asset?.total_return_pct || 0,
    notes: asset?.notes || "",
    isNFT: asset?.isNFT === true, // Trust the backend flag for NFT detection
    floorPrice: asset?.floorPrice || 0,
    imageUrl: asset?.imageUrl || null,
    tokenIds: asset?.tokenIds || [],
  };

  // Debug NFT detection
  if (safeAsset.isNFT) {
    console.log(
      `🖼️ [CARD DEBUG] Rendering NFT collection card: ${safeAsset.symbol} - ${safeAsset.name}`,
      {
        isNFT: safeAsset.isNFT,
        balance: safeAsset.balance,
        floorPrice: safeAsset.floorPrice,
        imageUrl: safeAsset.imageUrl,
        valueUSD: safeAsset.valueUSD,
        itemCount: Math.floor(safeAsset.balance),
      },
    );
  }

  const safeTotalValue = totalValue || 1; // Avoid division by zero
  const weight = ((safeAsset.valueUSD / safeTotalValue) * 100).toFixed(1);
  const isNFTCollection = safeAsset.isNFT;

  const returnColor =
    safeAsset.total_return_pct >= 0 ? "text-green-400" : "text-red-400";
  const returnIcon = safeAsset.total_return_pct >= 0 ? "📈" : "📉";

  return (
    <div
      className={`border rounded-xl overflow-hidden cursor-pointer transition-all duration-300 hover:shadow-lg ${
        isNFTCollection
          ? "bg-gradient-to-br from-purple-900/20 via-pink-900/20 to-gray-900 border-purple-500/30 hover:border-purple-400 hover:shadow-purple-500/20"
          : "bg-gradient-to-b from-gray-900 to-gray-950 border-gray-700 hover:border-gray-500 hover:shadow-purple-500/10"
      }`}
      onClick={onClick}
    >
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-3 min-w-0 flex-1">
            <div
              className={`w-10 h-10 sm:w-12 sm:h-12 flex items-center justify-center flex-shrink-0 shadow-lg overflow-hidden ${
                isNFTCollection
                  ? "rounded-lg bg-gradient-to-r from-pink-500 to-purple-500"
                  : "rounded-full bg-gradient-to-r " +
                    (safeAsset.total_return_pct >= 0
                      ? "from-green-500 to-emerald-500"
                      : "from-red-500 to-red-600")
              }`}
            >
              {isNFTCollection && safeAsset.imageUrl ? (
                <img
                  src={safeAsset.imageUrl}
                  alt={safeAsset.name}
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-white font-bold text-sm">
                  {isNFTCollection ? "🖼️" : safeAsset.symbol.slice(0, 2)}
                </span>
              )}
            </div>
            <div className="min-w-0 flex-1">
              <h3
                className={`font-medium text-sm sm:text-base truncate ${
                  isNFTCollection ? "text-purple-100" : "text-white"
                }`}
              >
                {safeAsset.name}
              </h3>
              <p className="text-xs sm:text-sm text-gray-400 truncate flex items-center">
                <span>{safeAsset.symbol}</span>
                {isNFTCollection && (
                  <span className="ml-2 px-2 py-0.5 bg-pink-500/20 text-pink-300 rounded-full text-xs border border-pink-500/30">
                    NFT
                  </span>
                )}
                {!isNFTCollection && safeAsset.total_return_pct !== 0 && (
                  <span className={`ml-2 font-bold ${returnColor}`}>
                    {returnIcon} {safeAsset.total_return_pct >= 0 ? "+" : ""}
                    {safeAsset.total_return_pct.toFixed(0)}%
                  </span>
                )}
                {isEditor &&
                  !isNFTCollection &&
                  safeAsset.purchase_price > 0 && (
                    <span
                      className="ml-2 px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded-full text-xs border border-blue-500/30"
                      title="Purchase price set manually"
                    >
                      📝
                    </span>
                  )}
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

        <div className="grid grid-cols-2 gap-2 text-xs sm:text-sm mb-3">
          <div>
            <span
              className={`block ${isNFTCollection ? "text-purple-300" : "text-gray-400"}`}
            >
              {isNFTCollection ? "Items" : "Balance"}
            </span>
            <span
              className={`font-mono ${isNFTCollection ? "text-purple-100" : "text-white"}`}
            >
              {isNFTCollection
                ? `${Math.floor(safeAsset.balance)} NFTs`
                : safeAsset.balance}
            </span>
          </div>
          <div>
            <span
              className={`block ${isNFTCollection ? "text-purple-300" : "text-gray-400"}`}
            >
              {isNFTCollection ? "Floor Price" : "Current Price"}
            </span>
            <span
              className={`font-mono ${isNFTCollection ? "text-purple-100" : "text-white"}`}
            >
              {isNFTCollection
                ? safeAsset.floorPrice > 0
                  ? `◎ ${safeAsset.floorPrice}`
                  : "Coming Soon"
                : `$${safeAsset.priceUSD.toLocaleString()}`}
            </span>
          </div>
          <div>
            <span
              className={`block ${isNFTCollection ? "text-purple-300" : "text-gray-400"}`}
            >
              {isNFTCollection ? "Collection Value" : "Current Value"}
            </span>
            <span
              className={`font-mono ${isNFTCollection ? "text-purple-100" : "text-white"}`}
            >
              {isNFTCollection
                ? safeAsset.valueUSD > 0
                  ? `$${safeAsset.valueUSD.toLocaleString()}`
                  : safeAsset.floorPrice > 0
                    ? `$${(safeAsset.floorPrice * parseFloat(safeAsset.balance)).toLocaleString()}`
                    : "Evaluating..."
                : `$${safeAsset.valueUSD.toLocaleString()}`}
            </span>
          </div>
          <div>
            <span
              className={`block ${isNFTCollection ? "text-purple-300" : "text-gray-400"}`}
            >
              {isNFTCollection ? "Portfolio %" : "Purchase Price"}
            </span>
            <span
              className={`font-mono ${isNFTCollection ? "text-purple-100" : "text-blue-400"}`}
            >
              {isNFTCollection
                ? `${weight}%`
                : `$${safeAsset.purchase_price.toFixed(4)}`}
            </span>
          </div>
        </div>
      </div>

      {/* Enhanced P&L section for tokens, NFT status for collections */}
      {isNFTCollection ? (
        <div className="px-4 py-3 bg-gradient-to-r from-purple-900/40 to-pink-900/40 border-t border-purple-700/50">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-purple-400"></span>
              <span className="text-xs sm:text-sm font-medium text-purple-200">
                Collection Status
              </span>
            </div>
            <div className="text-right">
              <div className="text-sm sm:text-base font-bold text-purple-300">
                {safeAsset.floorPrice > 0 ? "Active" : "Tracking"}
              </div>
              <div className="text-xs text-purple-400 opacity-80">
                {Math.floor(safeAsset.balance)} items
              </div>
            </div>
          </div>
        </div>
      ) : (
        safeAsset.total_invested > 0 && (
          <div
            className={`px-4 py-3 ${
              safeAsset.unrealized_pnl >= 0
                ? "bg-gradient-to-r from-green-900/40 to-emerald-900/40 border-t border-green-700/50"
                : "bg-gradient-to-r from-red-900/40 to-red-800/40 border-t border-red-700/50"
            }`}
          >
            <div className="flex justify-between items-center">
              <div className="flex items-center space-x-2">
                <span
                  className={`w-2 h-2 rounded-full ${
                    safeAsset.unrealized_pnl >= 0
                      ? "bg-green-400"
                      : "bg-red-400"
                  }`}
                ></span>
                <span className="text-xs sm:text-sm font-medium text-gray-300">
                  P&L
                </span>
              </div>
              <div className="text-right">
                <div
                  className={`text-sm sm:text-base font-bold ${returnColor}`}
                >
                  {safeAsset.unrealized_pnl >= 0 ? "+" : ""}$
                  {safeAsset.unrealized_pnl.toLocaleString()}
                </div>
                <div className={`text-xs ${returnColor} opacity-80`}>
                  {safeAsset.total_return_pct >= 0 ? "+" : ""}
                  {safeAsset.total_return_pct.toFixed(1)}%
                </div>
              </div>
            </div>
          </div>
        )
      )}
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

const WalletCard = ({
  wallet,
  walletData,
  assets,
  totalValue,
  performance,
}) => {
  const assetCount = assets ? assets.length : 0;
  const hasError =
    walletData?.status === "error" || walletData?.status === "timeout";

  // Get wallet-specific assets
  const walletAssets = assets
    ? assets.filter((asset) => {
        // Map assets to wallets based on token type
        if (wallet.network === "SOL") {
          return (
            asset.id === "solana" ||
            asset.symbol === "SOL" ||
            asset.symbol === "Fartcoin " ||
            asset.id.includes("pump") ||
            asset.name?.includes("pump") ||
            (asset.id.length > 40 && !asset.id.startsWith("0x"))
          ); // Solana addresses are longer and don't start with 0x
        } else if (wallet.network === "ETH") {
          return (
            asset.id.startsWith("0x") ||
            asset.id === "0x0000000000000000000000000000000000000000" ||
            asset.symbol === "ETH" ||
            asset.symbol === "WBTC" ||
            asset.symbol === "PENDLE" ||
            (asset.symbol === "PENGU" && asset.id.startsWith("0x"))
          ); // Only ETH-based PENGU
        }
        return false;
      })
    : [];

  const walletValue = walletAssets.reduce(
    (sum, asset) => sum + (asset.valueUSD || 0),
    0,
  );
  const walletAssetCount = walletAssets.length;

  return (
    <div
      className={`p-3 border rounded-lg ${wallet.network === "SOL" ? "border-purple-500/30 bg-purple-900/10" : "border-blue-500/30 bg-blue-900/10"}`}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-white flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${wallet.network === "SOL" ? "bg-purple-400" : "bg-blue-400"}`}
          ></span>
          {wallet.label}
        </h3>
        <span
          className={`text-xs px-2 py-1 rounded ${wallet.network === "SOL" ? "bg-purple-500/20 text-purple-300" : "bg-blue-500/20 text-blue-300"}`}
        >
          {wallet.network}
        </span>
      </div>

      <div className="text-xs text-gray-400 mb-2 font-mono break-all">
        {wallet.address.slice(0, 8)}...{wallet.address.slice(-8)}
      </div>

      {hasError ? (
        <div className="p-3 bg-red-900/20 border border-red-700/50 rounded-lg">
          <div className="text-red-400 text-xs font-medium mb-1">
            ⚠️ {wallet.network} Fetch Error
          </div>
          <div className="text-red-300 text-xs">
            {walletData?.errorMessage ||
              `Unable to fetch ${wallet.network} data. This could be due to API limits, network issues, or wallet address format problems.`}
          </div>
          <div className="text-red-400 text-xs mt-1">
            💡 Try updating the portfolio again or check if the {wallet.network}{" "}
            address is valid.
          </div>
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-3 gap-2 text-xs sm:text-sm mb-2">
            <div>
              <span className="text-gray-400 block">Total Value</span>
              <span className="text-white font-mono">
                ${walletValue.toLocaleString()}
              </span>
            </div>
            <div>
              <span className="text-gray-400 block">Assets</span>
              <span className="text-white font-mono">{walletAssetCount}</span>
            </div>
            <div>
              <span className="text-gray-400 block">24h Change</span>
              <span
                className={`font-mono ${performance >= 0 ? "text-green-400" : "text-red-400"}`}
              >
                {performance >= 0 ? "+" : ""}
                {performance.toFixed(2)}%
              </span>
            </div>
          </div>

          {/* Show top assets for this wallet */}
          {walletAssets.length > 0 && (
            <div className="border-t border-gray-700/50 pt-2">
              <div className="text-xs text-gray-400 mb-1">Top Assets:</div>
              {walletAssets
                .filter((asset) => asset.valueUSD > 0)
                .sort((a, b) => b.valueUSD - a.valueUSD)
                .slice(0, 3)
                .map((asset) => (
                  <div
                    key={asset.id}
                    className="flex justify-between text-xs py-1"
                  >
                    <span className="text-gray-300 truncate max-w-[120px]">
                      {asset.symbol}
                    </span>
                    <span className="text-white font-mono">
                      ${asset.valueUSD.toLocaleString()}
                    </span>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Wallet Details Modal
const WalletModal = ({ wallet, onClose, walletData, portfolioData }) => {
  if (!wallet) return null;

  const walletAssets = walletData?.assets || [];
  const totalValue = walletAssets.reduce(
    (sum, asset) => sum + asset.valueUSD,
    0,
  );
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
                <h2 className="text-lg sm:text-xl font-bold text-white">
                  {wallet.label}
                </h2>
                <p className="text-sm text-gray-400 font-mono break-all">
                  {wallet.address}
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Wallet Metrics */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">Total Value</div>
              <div className="text-xl font-bold text-white">
                ${totalValue.toLocaleString()}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">Assets</div>
              <div className="text-xl font-bold text-white">
                {walletAssets.length}
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">24h Change</div>
              <div
                className={`text-xl font-bold ${performance >= 0 ? "text-green-400" : "text-red-400"}`}
              >
                {performance >= 0 ? "+" : ""}
                {performance.toFixed(2)}%
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">Network</div>
              <div className="text-xl font-bold text-white">
                {wallet.network}
              </div>
            </div>
          </div>

          {/* Performance Chart */}
          {performanceHistory.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-4 mb-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                Wallet Performance
              </h3>
              <div className="h-48">
                <PortfolioChart data={performanceHistory} />
              </div>
            </div>
          )}

          {/* Assets in Wallet */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">
              Assets in Wallet ({walletAssets.length})
            </h3>
            {walletAssets.length === 0 ? (
              <div className="bg-gray-800 rounded-lg p-8 text-center">
                <div className="text-gray-400 mb-2">
                  No assets found in this wallet
                </div>
                <div className="text-sm text-gray-500">
                  This wallet may be empty or data hasn't been fetched yet
                </div>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {walletAssets.map((asset, index) => (
                  <div key={index} className="bg-gray-800 rounded-lg p-4">
                    <div className="flex items-center space-x-3 mb-3">
                      <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                        <span className="text-white font-bold text-xs">
                          {asset.symbol.slice(0, 2)}
                        </span>
                      </div>
                      <div>
                        <div className="font-medium text-white text-sm">
                          {asset.name}
                        </div>
                        <div className="text-xs text-gray-400">
                          {asset.symbol}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-400">Balance:</span>
                        <span className="text-white font-mono">
                          {asset.balance}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Value:</span>
                        <span className="text-green-400 font-mono">
                          ${asset.valueUSD.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-400">Price:</span>
                        <span className="text-white font-mono">
                          ${asset.priceUSD.toFixed(4)}
                        </span>
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

// Returns Analysis Modal
const ReturnsModal = ({ isOpen, onClose, portfolioData }) => {
  const [returnsData, setReturnsData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchReturnsData();
    }
  }, [isOpen]);

  const fetchReturnsData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/portfolio/returns`);
      if (response.ok) {
        const data = await response.json();
        setReturnsData(data);
      }
    } catch (error) {
      console.error("Error fetching returns data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg sm:text-xl font-bold text-white">
              📊 Portfolio Returns Analysis
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {loading ? (
            <div className="text-center py-8">
              <LoadingSpinner status="Loading returns analysis..." />
            </div>
          ) : returnsData ? (
            <div className="space-y-6">
              {/* Portfolio Summary */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-xs text-gray-400 mb-1">
                    Total Invested
                  </div>
                  <div className="text-xl font-bold text-white">
                    $
                    {returnsData.portfolio_metrics.total_invested.toLocaleString()}
                  </div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-xs text-gray-400 mb-1">
                    Current Value
                  </div>
                  <div className="text-xl font-bold text-white">
                    $
                    {returnsData.portfolio_metrics.total_current_value.toLocaleString()}
                  </div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-xs text-gray-400 mb-1">Total Return</div>
                  <div
                    className={`text-xl font-bold ${returnsData.portfolio_metrics.overall_return_pct >= 0 ? "text-green-400" : "text-red-400"}`}
                  >
                    {returnsData.portfolio_metrics.overall_return_pct >= 0
                      ? "+"
                      : ""}
                    {returnsData.portfolio_metrics.overall_return_pct.toFixed(
                      1,
                    )}
                    %
                  </div>
                </div>
                <div className="bg-gray-800 rounded-lg p-4">
                  <div className="text-xs text-gray-400 mb-1">
                    Unrealized P&L
                  </div>
                  <div
                    className={`text-xl font-bold ${returnsData.portfolio_metrics.total_unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"}`}
                  >
                    $
                    {returnsData.portfolio_metrics.total_unrealized_pnl.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Top Performers */}
              <div>
                <h3 className="text-lg font-semibold text-white mb-4">
                  🚀 Top Performers
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                  {returnsData.top_performers
                    .slice(0, 6)
                    .map((performer, index) => (
                      <div
                        key={index}
                        className="bg-green-900/20 border border-green-700/50 rounded-lg p-4"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-white">
                            {performer.symbol}
                          </span>
                          <span className="text-xs text-green-400">
                            #{index + 1}
                          </span>
                        </div>
                        <div className="text-xs text-gray-400 mb-1">
                          {performer.name}
                        </div>
                        <div className="text-lg font-bold text-green-400">
                          +{performer.return_pct.toFixed(1)}%
                        </div>
                        <div className="text-sm text-gray-300">
                          ${performer.unrealized_pnl.toLocaleString()} profit
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {/* Worst Performers */}
              {returnsData.worst_performers.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-white mb-4">
                    📉 Underperformers
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {returnsData.worst_performers.map((performer, index) => (
                      <div
                        key={index}
                        className="bg-red-900/20 border border-red-700/50 rounded-lg p-4"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-white">
                            {performer.symbol}
                          </span>
                          <span className="text-xs text-red-400">⚠️</span>
                        </div>
                        <div className="text-xs text-gray-400 mb-1">
                          {performer.name}
                        </div>
                        <div className="text-lg font-bold text-red-400">
                          {performer.return_pct.toFixed(1)}%
                        </div>
                        <div className="text-sm text-gray-300">
                          ${performer.unrealized_pnl.toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              No returns data available
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

// Enhanced Asset Details Modal with returns data and purchase price override
const AssetModal = ({
  asset,
  onClose,
  onUpdateNotes,
  onUpdatePurchasePrice,
  isEditor,
}) => {
  const [notes, setNotes] = useState(asset?.notes || "");
  const [purchasePrice, setPurchasePrice] = useState(
    (asset?.purchase_price || 0).toString(),
  );
  const [isUpdatingPrice, setIsUpdatingPrice] = useState(false);
  const [priceError, setPriceError] = useState("");

  if (!asset) return null;

  const handleSave = async () => {
    if (isEditor && purchasePrice !== (asset?.purchase_price || 0).toString()) {
      await handlePurchasePriceUpdate();
    }
    onUpdateNotes(asset.id, notes);
    onClose();
  };

  const handlePurchasePriceUpdate = async () => {
    setPriceError("");

    // Validate input
    const priceValue = parseFloat(purchasePrice);
    if (isNaN(priceValue)) {
      setPriceError("Please enter a valid number");
      return;
    }

    if (priceValue < 0) {
      setPriceError("Purchase price cannot be negative");
      return;
    }

    // Allow zero for airdrops or free tokens, but warn user
    if (
      priceValue === 0 &&
      !confirm(
        "Setting purchase price to $0. This is typically used for airdrops or free tokens. Continue?",
      )
    ) {
      return;
    }

    setIsUpdatingPrice(true);

    try {
      const success = await onUpdatePurchasePrice(asset.symbol, priceValue);
      if (success) {
        // Update local state to reflect the change immediately
        asset.purchase_price = priceValue;
        asset.total_invested = (asset.balance || 0) * priceValue;
        asset.unrealized_pnl = (asset.valueUSD || 0) - asset.total_invested;
        asset.total_return_pct =
          asset.total_invested > 0
            ? (((asset.valueUSD || 0) - asset.total_invested) /
                asset.total_invested) *
              100
            : 0;
      }
    } catch (error) {
      console.error("Purchase price update error:", error);
      setPriceError(`Failed to update price: ${error.message}`);
    }

    // Always reset loading state, even if there was an error
    setIsUpdatingPrice(false);
  };

  const returnColor =
    (asset.total_return_pct || 0) >= 0 ? "text-green-400" : "text-red-400";
  const pnlColor =
    (asset.unrealized_pnl || 0) >= 0 ? "text-green-400" : "text-red-400";

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg sm:text-xl font-bold text-white">
              {asset.name}
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Investment Metrics */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">Total Return</div>
              <div className={`text-lg font-bold ${returnColor}`}>
                {(asset.total_return_pct || 0) >= 0 ? "+" : ""}
                {(asset.total_return_pct || 0).toFixed(1)}%
              </div>
            </div>
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="text-xs text-gray-400 mb-1">Unrealized P&L</div>
              <div className={`text-lg font-bold ${pnlColor}`}>
                ${(asset.unrealized_pnl || 0).toLocaleString()}
              </div>
            </div>
          </div>

          <div className="space-y-3 mb-4 text-sm sm:text-base">
            <div className="flex justify-between">
              <span className="text-gray-400">Balance:</span>
              <span className="text-white font-mono">
                {asset?.balance || "0"} {asset?.symbol || "N/A"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Current Price:</span>
              <span className="text-white font-mono">
                ${(asset?.priceUSD || 0).toFixed(4)}
              </span>
            </div>

            {/* Purchase Price - Editable in editor mode */}
            <div className="flex justify-between items-center">
              <span className="text-gray-400">Purchase Price:</span>
              {isEditor ? (
                <div className="flex items-center space-x-2">
                  <span className="text-gray-400">$</span>
                  <input
                    type="number"
                    value={purchasePrice}
                    onChange={(e) => {
                      setPurchasePrice(e.target.value);
                      setPriceError("");
                    }}
                    onBlur={handlePurchasePriceUpdate}
                    onKeyPress={(e) =>
                      e.key === "Enter" && handlePurchasePriceUpdate()
                    }
                    className="w-24 p-1 bg-gray-800 border border-gray-600 rounded text-blue-400 font-mono text-sm focus:border-blue-500 focus:outline-none"
                    step="0.0001"
                    min="0"
                    disabled={isUpdatingPrice}
                  />
                  {isUpdatingPrice && (
                    <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                  )}
                </div>
              ) : (
                <span className="text-blue-400 font-mono">
                  ${(asset?.purchase_price || 0).toFixed(4)}
                </span>
              )}
            </div>

            {priceError && (
              <div className="text-red-400 text-xs">{priceError}</div>
            )}

            <div className="flex justify-between">
              <span className="text-gray-400">Total Invested:</span>
              <span className="text-blue-400 font-mono">
                ${(asset?.total_invested || 0).toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Current Value:</span>
              <span className="text-green-400 font-mono">
                ${(asset?.valueUSD || 0).toLocaleString()}
              </span>
            </div>
          </div>

          {isEditor && (
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2 text-gray-300">
                Notes:
              </label>
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
    <span className="text-sm">{status || "Loading..."}</span>
  </div>
);

// Settings Modal Component
const SettingsModal = ({
  isOpen,
  onClose,
  isEditor,
  password,
  setPassword,
  onPasswordCheck,
  onEditorExit,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-xl max-w-md w-full">
        <div className="p-4 sm:p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg sm:text-xl font-bold text-white">
              Settings
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {!isEditor ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-base font-semibold text-white mb-2">
                  🔐 Editor Access
                </h3>
                <p className="text-sm text-gray-400 mb-4">
                  Enter access key to unlock dashboard editing features
                </p>
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
                <h3 className="text-base font-semibold text-green-400 mb-2">
                  ✅ Editor Mode Active
                </h3>
                <p className="text-sm text-gray-300 mb-4">
                  You're currently in editor mode with full dashboard access.
                </p>
                <div className="text-sm text-green-400 mb-4">
                  🔧 Editor features enabled: Hide assets, manage wallets,
                  update notes
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

// ================================================================================================
// API BASE URL CONFIGURATION - CRITICAL FOR DEPLOYMENT SUCCESS
// ================================================================================================
//
// This function determines the correct API base URL for different environments.
//
// PRODUCTION DEPLOYMENT (w3e.info, .replit.app):
// - Backend runs on port 80 (same as frontend)
// - Use same origin - NO PORT NUMBER needed
// - Example: https://w3e.info (not https://w3e.info:8000)
//
// DEVELOPMENT (.replit.dev):
// - Backend runs on port 8000, frontend on port 5000
// - Must specify port 8000 for API calls
// - Example: https://abc.replit.dev:8000
//
// LOCAL DEVELOPMENT:
// - Backend on localhost:8000, frontend on localhost:5000
// - Use localhost:8000 for API calls
//
// DEPLOYMENT FAILURE PREVENTION:
// - Production deployments MUST NOT include port numbers in API URLs
// - Backend MUST run on port 80 in production (see server/main.py)
// - If frontend tries to connect to :8000 in production, it will fail
// ================================================================================================
const getAPIBaseURL = () => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;

    // Production deployment URLs - use same origin (NO PORT!)
    // CRITICAL: Do not add port numbers here - backend runs on port 80
    if (hostname === "w3e.info" || hostname.includes(".replit.app")) {
      return `${protocol}//${hostname}`;
    }

    // Development URLs - localhost and 127.x.x.x
    if (hostname === "localhost" || hostname.startsWith("127.")) {
      // Backend runs on port 8000 in development
      return "http://localhost:80";
    }

    // Replit development URLs - .replit.dev domains
    if (hostname.includes(".replit.dev")) {
      // Backend runs on port 8000, frontend on port 5000
      return `${protocol}//${hostname}`;
    }
  }

  // Fallback for any other case
  return "http://localhost:80";
};

// API Configuration for Replit environment
const API_BASE_URL = getAPIBaseURL();

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
  const [showReturnsModal, setShowReturnsModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [portfolioData, setPortfolioData] = useState({
    balanceHistory: [],
    assets: [],
  });
  const [walletData, setWalletData] = useState(() => {
    const saved = localStorage.getItem("walletData");
    return saved ? JSON.parse(saved) : {};
  });
  const [lastUpdated, setLastUpdated] = useState(() => {
    const saved = localStorage.getItem("lastUpdated");
    return saved ? new Date(saved) : null;
  });

  const correctPassword = "bullrun";

  // Function to get live status with real-time updates
  const getLiveStatus = () => {
    // If we have portfolio data, don't show "No data"
    const hasData = portfolioData.assets && portfolioData.assets.length > 0;

    if (!lastUpdated && !hasData) {
      return {
        text: "No data",
        color: "text-gray-400",
        dot: "bg-gray-400",
      };
    }

    if (!lastUpdated && hasData) {
      return {
        text: "Data loaded",
        color: "text-blue-400",
        dot: "bg-blue-400",
      };
    }

    const now = new Date();
    const diffMs = now - lastUpdated;
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

    if (diffMinutes < 1) {
      return {
        text: "Live now",
        color: "text-green-400",
        dot: "bg-green-400 animate-pulse",
      };
    } else if (diffMinutes < 5) {
      return {
        text: `${diffMinutes}m ago`,
        color: "text-green-400",
        dot: "bg-green-400",
      };
    } else if (diffMinutes < 30) {
      return {
        text: `${diffMinutes}m ago`,
        color: "text-yellow-400",
        dot: "bg-yellow-400",
      };
    } else if (diffHours < 1) {
      return {
        text: `${diffMinutes}m ago`,
        color: "text-orange-400",
        dot: "bg-orange-400",
      };
    } else if (diffHours < 24) {
      return {
        text: `${diffHours}h ago`,
        color: "text-red-400",
        dot: "bg-red-400",
      };
    } else {
      const diffDays = Math.floor(diffHours / 24);
      return {
        text: `${diffDays}d ago`,
        color: "text-red-500",
        dot: "bg-red-500",
      };
    }
  };

  // Update live status every minute
  const [, forceUpdate] = useState({});
  useEffect(() => {
    const interval = setInterval(() => {
      forceUpdate({});
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

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
    setTimeout(() => setUpdateStatus(""), 3000);
  };

  const toggleHiddenAsset = async (asset) => {
    try {
      const isCurrentlyHidden = hiddenAssets.includes(asset.id);

      if (isCurrentlyHidden) {
        // Unhide the asset
        const response = await fetch(
          `${API_BASE_URL}/api/assets/hide/${asset.id}`,
          {
            method: "DELETE",
          },
        );

        if (response.ok) {
          setHiddenAssets((prev) => {
            const newHiddenAssets = prev.filter((id) => id !== asset.id);
            localStorage.setItem(
              "hiddenAssets",
              JSON.stringify(newHiddenAssets),
            );
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
          name: asset.name,
        });

        const response = await fetch(
          `${API_BASE_URL}/api/assets/hide?${params}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          },
        );

        if (response.ok) {
          setHiddenAssets((prev) => {
            const newHiddenAssets = [...prev, asset.id];
            localStorage.setItem(
              "hiddenAssets",
              JSON.stringify(newHiddenAssets),
            );
            return newHiddenAssets;
          });
          console.log(`✅ Hid asset: ${asset.symbol}`);
        } else {
          const errorText = await response.text();
          throw new Error(
            `Failed to hide asset: ${response.status} - ${errorText}`,
          );
        }
      }
    } catch (error) {
      console.error("Error toggling hidden asset:", error);
      alert(`Failed to update asset visibility: ${error.message}`);
    }
  };

  const updateNotes = async (assetId, notes) => {
    if (!assetId) {
      setSelectedAsset(null);
      return;
    }

    try {
      const asset = portfolioData.assets.find((a) => a.id === assetId);
      if (!asset) return;

      // Choose the appropriate endpoint based on asset type
      let endpoint;
      if (asset.isNFT) {
        endpoint = `${API_BASE_URL}/api/nfts/${asset.id}/notes?notes=${encodeURIComponent(notes)}`;
      } else {
        endpoint = `${API_BASE_URL}/api/assets/${asset.symbol}/notes?notes=${encodeURIComponent(notes)}`;
      }

      const response = await fetch(endpoint, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to update notes");
      }

      setPortfolioData((prev) => ({
        ...prev,
        assets: prev.assets.map((a) =>
          a.id === assetId ? { ...a, notes } : a,
        ),
      }));
    } catch (error) {
      console.error("Error updating notes:", error);
      alert(`Failed to update notes: ${error.message}`);
    }
  };

  const updatePurchasePrice = async (symbol, purchasePrice) => {
    if (!symbol) {
      throw new Error("Symbol is required");
    }

    // Validate purchase price
    if (typeof purchasePrice !== "number" || isNaN(purchasePrice)) {
      throw new Error("Invalid purchase price");
    }

    if (purchasePrice < 0) {
      throw new Error("Purchase price cannot be negative");
    }

    try {
      addDebugInfo(`Updating purchase price for ${symbol}: $${purchasePrice}`);

      // Find the asset to determine if it's an NFT
      const asset = portfolioData.assets.find(a => a.symbol === symbol);
      const isNFT = asset?.isNFT || false;
      
      // Choose the appropriate endpoint
      let endpoint;
      if (isNFT) {
        endpoint = `${API_BASE_URL}/api/nfts/${asset.id}/purchase_price`;
      } else {
        endpoint = `${API_BASE_URL}/api/assets/${symbol}/purchase_price`;
      }

      const response = await fetch(endpoint, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          purchase_price: purchasePrice,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage;
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || "Failed to update purchase price";
        } catch {
          errorMessage = `HTTP ${response.status}: ${errorText}`;
        }
        throw new Error(errorMessage);
      }

      // Update local state immediately for better UX
      setPortfolioData((prev) => ({
        ...prev,
        assets: prev.assets.map((asset) => {
          if (asset.symbol === symbol) {
            if (asset.isNFT) {
              // NFT calculation
              const itemCount = parseFloat(asset.balance) || 0;
              const currentValue = asset.valueUSD || 0;
              const totalInvested = itemCount * purchasePrice;
              const unrealizedPnl = currentValue - totalInvested;
              const returnPct = totalInvested > 0 ? (unrealizedPnl / totalInvested) * 100 : 0;

              return {
                ...asset,
                purchase_price: purchasePrice,
                total_invested: totalInvested,
                unrealized_pnl: unrealizedPnl,
                total_return_pct: returnPct,
              };
            } else {
              // Regular asset calculation
              const balance = parseFloat(asset.balance) || 0;
              const currentValue = asset.valueUSD || 0;
              const totalInvested = balance * purchasePrice;
              const unrealizedPnl = currentValue - totalInvested;
              const returnPct = totalInvested > 0 ? (unrealizedPnl / totalInvested) * 100 : 0;

              return {
                ...asset,
                purchase_price: purchasePrice,
                total_invested: totalInvested,
                unrealized_pnl: unrealizedPnl,
                total_return_pct: returnPct,
              };
            }
          }
          return asset;
        }),
      }));

      addDebugInfo(`✅ Purchase price updated for ${isNFT ? 'NFT collection' : 'asset'} ${symbol}`);

      // Show success message briefly
      const assetType = isNFT ? "NFT collection" : "asset";
      setUpdateStatus(
        `✅ Updated ${assetType} ${symbol} purchase price to $${purchasePrice.toFixed(4)}`,
      );
      setTimeout(() => setUpdateStatus(""), 3000);

      return true;
    } catch (error) {
      console.error("Error updating purchase price:", error);
      addDebugInfo(
        `❌ Error updating purchase price for ${symbol}: ${error.message}`,
      );
      throw error; // Re-throw so the modal can handle it
    }
  };

  // Wallet addresses for the fund - stored in state forThis commit addresses a syntax error in the `addWallet` function, specifically ensuring that the API_BASE_URL is correctly used within the template literal for the fetch request. dynamic management
  const [walletAddresses, setWalletAddresses] = useState(() => {
    const saved = localStorage.getItem("fundWallets");
    return saved
      ? JSON.parse(saved)
      : [
          {
            id: 1,
            address: "0x0f82438E71EF21e07b6A5871Df2a481B2Dd92A98",
            label: "Ethereum Safe Multisig",
            network: "ETH",
          },
          {
            id: 2,
            address: "4ZE7D7ecU7tSvA5iJVCVp6MprguDqy7tvXguE64T9Twb",
            label: "Solana EOA",
            network: "SOL",
          },
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
      addDebugInfo(`Adding wallet: ${newWalletLabel} (${newWalletNetwork})`);

      const response = await fetch(`${API_BASE_URL}/api/wallets`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          address: newWalletAddress.trim(),
          label: newWalletLabel.trim(),
          network: newWalletNetwork,
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage;
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || "Failed to add wallet";
        } catch {
          errorMessage = `HTTP ${response.status}: ${errorText}`;
        }
        throw new Error(errorMessage);
      }

      const newWallet = await response.json();
      addDebugInfo(
        `✅ Wallet added to backend: ${newWallet.id} - ${newWallet.label}`,
      );

      // Update local state
      const updatedWallets = [...walletAddresses, newWallet];
      setWalletAddresses(updatedWallets);
      localStorage.setItem("fundWallets", JSON.stringify(updatedWallets));

      // Clear form
      setNewWalletAddress("");
      setNewWalletLabel("");
      setNewWalletNetwork("ETH");

      addDebugInfo(`✅ Wallet "${newWallet.label}" added successfully`);

      // Show success message
      setUpdateStatus(`✅ Added wallet: ${newWallet.label}`);
      setTimeout(() => setUpdateStatus(""), 3000);
    } catch (error) {
      console.error("Error adding wallet:", error);
      addDebugInfo(`❌ Error adding wallet: ${error.message}`);
      alert(`Failed to add wallet: ${error.message}`);
    }
  };

  const removeWallet = async (walletId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/wallets/${walletId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to remove wallet");
      }

      const updatedWallets = walletAddresses.filter(
        (wallet) => wallet.id !== walletId,
      );
      setWalletAddresses(updatedWallets);
      localStorage.setItem("fundWallets", JSON.stringify(updatedWallets));

      // Remove wallet data from local state
      const newWalletData = { ...walletData };
      delete newWalletData[walletId];
      setWalletData(newWalletData);
      localStorage.setItem("walletData", JSON.stringify(newWalletData));
    } catch (error) {
      console.error("Error removing wallet:", error);
      alert(`Failed to remove wallet: ${error.message}`);
    }
  };

  // Status tracking state
  const [updateStatus, setUpdateStatus] = useState("");
  const [updateError, setUpdateError] = useState("");
  const [debugInfo, setDebugInfo] = useState([]);
  const [walletStatus, setWalletStatus] = useState([]);

  // Debug logging function
  const addDebugInfo = (message, data = null) => {
    const timestamp = new Date().toLocaleTimeString();
    const debugEntry = { timestamp, message, data };
    console.log(`🐛 [${timestamp}] ${message}`, data || "");
    setDebugInfo((prev) => [...prev.slice(-9), debugEntry]); // Keep last 10 entries
  };

  // Load saved portfolio data on startup and sync wallets
  useEffect(() => {
    const loadPortfolioAndSyncWallets = async (retryCount = 0) => {
      const maxRetries = 3;

      try {
        addDebugInfo("Starting portfolio data load", {
          retryCount,
          API_BASE_URL,
        });

        // Test backend connection first with longer timeout
        addDebugInfo("Testing backend connection...");
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

        const healthResponse = await fetch(`${API_BASE_URL}/health`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!healthResponse.ok) {
          throw new Error(`Backend not ready (${healthResponse.status})`);
        }
        addDebugInfo("✅ Backend connection successful");

        // Load hidden assets from backend
        try {
          addDebugInfo("Loading hidden assets...");
          const hiddenResponse = await fetch(
            `${API_BASE_URL}/api/assets/hidden`,
          );
          if (hiddenResponse.ok) {
            const hiddenData = await hiddenResponse.json();
            const hiddenIds = hiddenData.map((asset) => asset.token_address);
            setHiddenAssets(hiddenIds);
            localStorage.setItem("hiddenAssets", JSON.stringify(hiddenIds));
            addDebugInfo(
              `✅ Loaded ${hiddenIds.length} hidden assets`,
              hiddenIds,
            );
          } else {
            addDebugInfo(`⚠️ Hidden assets response: ${hiddenResponse.status}`);
          }
        } catch (error) {
          addDebugInfo("❌ Error loading hidden assets", error.message);
        }

        // Load saved portfolio data
        addDebugInfo("Loading portfolio data...");
        const portfolioResponse = await fetch(`${API_BASE_URL}/api/portfolio`);

        if (!portfolioResponse.ok) {
          throw new Error(
            `Portfolio fetch failed: ${portfolioResponse.status} ${portfolioResponse.statusText}`,
          );
        }

        const savedData = await portfolioResponse.json();
        addDebugInfo("📊 Raw portfolio data received", savedData);

        console.log("🔍 [FRONTEND DEBUG] Full backend response:", savedData);
        console.log("🔍 [FRONTEND DEBUG] Assets array:", savedData.assets);
        console.log(
          "🔍 [FRONTEND DEBUG] Assets length:",
          savedData.assets?.length,
        );

        if (savedData.assets && savedData.assets.length > 0) {
          console.log("🔄 [FRONTEND DEBUG] Starting asset transformation...");
          console.log(" ��� [NFT SEARCH] Looking for NFTs in backend data...");

          // First pass - identify NFTs
          const nftsFound = savedData.assets.filter(
            (asset) =>
              asset.is_nft === true ||
              asset.is_nft === 1 ||
              asset.symbol?.includes("NFT") ||
              asset.name?.includes("Collection") ||
              (asset.nft_metadata && asset.nft_metadata !== null),
          );

          console.log(
            `🖼️ [NFT SEARCH] Found ${nftsFound.length} potential NFTs:`,
            nftsFound.map((nft) => ({
              symbol: nft.symbol,
              name: nft.name,
              is_nft: nft.is_nft,
              has_metadata: !!nft.has_metadata,
            })),
          );

          // Process NFTs from savedData.nfts if available
          const processedNFTs = (savedData.nfts || []).map((nft) => ({
            id: nft.id || nft.contract_address,
            contract_address: nft.contract_address,
            symbol: nft.symbol,
            name: nft.name,
            item_count: nft.item_count || 1,
            token_ids: nft.token_ids || [],
            floor_price_usd: nft.floor_price_usd || 0,
            total_value_usd: nft.total_value_usd || 0,
            image_url: nft.image_url,
            purchase_price: nft.purchase_price || 0,
            total_invested: nft.total_invested || 0,
            realized_pnl: nft.realized_pnl || 0,
            unrealized_pnl: nft.unrealized_pnl || 0,
            total_return_pct: nft.total_return_pct || 0,
            notes: nft.notes || "",
          }));

          console.log(`🖼️ [NFT DEBUG] Processed ${processedNFTs.length} NFTs from backend:`, processedNFTs);

          const transformedAssets = savedData.assets.map((asset, index) => {
            console.log(
              `🔄 [FRONTEND DEBUG] Transforming asset ${index + 1}:`,
              asset,
            );

            // Parse NFT metadata if present
            let nftMetadata = null;
            if (asset.nft_metadata) {
              try {
                nftMetadata = JSON.parse(asset.nft_metadata);
                console.log(
                  `🖼️ [NFT DEBUG] Parsed metadata for ${asset.symbol}:`,
                  nftMetadata,
                );
              } catch (e) {
                console.warn("Failed to parse NFT metadata:", e);
              }
            }

            // Enhanced NFT detection - check backend flag first
            const isNFT =
              asset.is_nft === true ||
              asset.is_nft === 1 ||
              asset.symbol?.includes("NFT") ||
              asset.name?.includes("Collection") ||
              (asset.balance_formatted &&
                asset.balance_formatted.includes("NFTs")) ||
              (nftMetadata && nftMetadata.token_ids) ||
              false;

            if (isNFT) {
              console.log(
                `🖼️ [NFT DEBUG] Detected NFT: ${asset.symbol} - ${asset.name} - Backend isNFT: ${asset.is_nft}`,
              );
              console.log(
                `🖼️ [NFT DEBUG] NFT Floor Price: ${asset.floor_price}, Image: ${asset.image_url}`,
              );
              console.log(`🖼️ [NFT DEBUG] NFT Metadata: ${asset.nft_metadata}`);
            }

            const transformed = {
              id: asset.id,
              name: asset.name,
              symbol: asset.symbol,
              balance: asset.balance_formatted || asset.balance,
              priceUSD: asset.price_usd || 0,
              valueUSD: asset.value_usd || 0,
              purchase_price: asset.purchase_price || 0,
              total_invested: asset.total_invested || 0,
              realized_pnl: asset.realized_pnl || 0,
              unrealized_pnl: asset.unrealized_pnl || 0,
              total_return_pct: asset.total_return_pct || 0,
              notes: asset.notes || "",
              isNFT: isNFT,
              floorPrice: asset.floor_price || nftMetadata?.floor_price || 0,
              imageUrl: asset.image_url || nftMetadata?.image_url || null,
              performance24h: asset.price_change_24h || 0,
              tokenIds: nftMetadata?.token_ids || [],
              nftMetadata: asset.nft_metadata || null,
            };

            if (isNFT) {
              console.log(`🖼️ [NFT DEBUG] Final NFT asset:`, transformed);
            } else {
              console.log(`✅ [FRONTEND DEBUG] Transformed to:`, transformed);
            }
            return transformed;
          });
          console.log(
            "🎯 [FRONTEND DEBUG] Final transformed assets:",
            transformedAssets,
          );

          const savedTotalValue = savedData.total_value || 0;

          // Generate balance history based on saved data
          const balanceHistory =
            savedTotalValue > 0
              ? [
                  { value: savedTotalValue * 0.92 },
                  { value: savedTotalValue * 0.95 },
                  { value: savedTotalValue * 0.88 },
                  { value: savedTotalValue * 0.96 },
                  { value: savedTotalValue },
                ]
              : [{ value: 0 }];

          const portfolioUpdate = {
            assets: transformedAssets,
            nfts: processedNFTs,
            balanceHistory: balanceHistory,
            totalValue: savedTotalValue,
            performance24h: savedData.performance_24h || 0,
          };

          setPortfolioData(portfolioUpdate);
          addDebugInfo(`✅ Portfolio data set successfully`, {
            assetCount: transformedAssets.length,
            totalValue: savedTotalValue,
            sampleAsset: transformedAssets[0],
          });
        } else {
          addDebugInfo("⚠️ No assets found in portfolio data", savedData);
        }

        // Get current wallets from backend and sync with local state
        addDebugInfo("Loading wallets from backend...");
        const walletsResponse = await fetch(`${API_BASE_URL}/api/wallets`);
        if (walletsResponse.ok) {
          const backendWallets = await walletsResponse.json();
          addDebugInfo(
            `📋 Backend has ${backendWallets.length} wallets`,
            backendWallets,
          );

          // Update local wallet state to match backend, but preserve default wallets
          if (backendWallets.length > 0) {
            // Use backend wallets as source of truth
            setWalletAddresses(backendWallets);
            localStorage.setItem("fundWallets", JSON.stringify(backendWallets));
            addDebugInfo("✅ Using backend wallets as source of truth");
          } else {
            // Backend is empty, sync local wallets to backend
            addDebugInfo("Backend has no wallets, syncing local wallets...");
            const currentWallets = [...walletAddresses];
            const syncPromises = currentWallets.map(async (wallet) => {
              try {
                const response = await fetch(`${API_BASE_URL}/api/wallets`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    address: wallet.address,
                    label: wallet.label,
                    network: wallet.network,
                  }),
                });

                if (response.ok) {
                  const newWallet = await response.json();
                  addDebugInfo(`✅ Synced wallet to backend: ${wallet.label}`);
                  return newWallet;
                } else {
                  addDebugInfo(`❌ Failed to sync wallet: ${wallet.label}`);
                  return null;
                }
              } catch (error) {
                addDebugInfo(
                  `❌ Error syncing wallet ${wallet.label}: ${error.message}`,
                );
                return null;
              }
            });

            // Wait for all syncs to complete
            const syncedWallets = await Promise.all(syncPromises);
            const successfulWallets = syncedWallets.filter((w) => w !== null);

            if (successfulWallets.length > 0) {
              setWalletAddresses(successfulWallets);
              localStorage.setItem(
                "fundWallets",
                JSON.stringify(successfulWallets),
              );
              addDebugInfo(
                `✅ Synced ${successfulWallets.length} wallets to backend`,
              );
            }
          }

          // Load wallet status information
          try {
            const statusResponse = await fetch(
              `${API_BASE_URL}/api/wallets/status`,
            );
            if (statusResponse.ok) {
              const statusData = await statusResponse.json();
              setWalletStatus(statusData);
              addDebugInfo(
                `📊 Loaded wallet status for ${statusData.length} wallets`,
              );
            }
          } catch (error) {
            addDebugInfo("⚠️ Could not load wallet status", error.message);
          }

          // If backend is empty but we have local wallets, sync them
          if (backendWallets.length === 0 && walletAddresses.length > 0) {
            addDebugInfo("Syncing local wallets to backend...");
            for (const wallet of walletAddresses) {
              try {
                const syncResponse = await fetch(
                  `${API_BASE_URL}/api/wallets`,
                  {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                      address: wallet.address,
                      label: wallet.label,
                      network: wallet.network,
                    }),
                  },
                );

                if (syncResponse.ok) {
                  addDebugInfo(`✅ Synced wallet: ${wallet.label}`);
                } else {
                  const errorData = await syncResponse.json();
                  addDebugInfo(
                    `❌ Failed to sync wallet ${wallet.label}: ${errorData.detail || "Unknown error"}`,
                  );
                }
              } catch (error) {
                addDebugInfo(
                  `❌ Error syncing wallet ${wallet.label}: ${error.message}`,
                );
              }
            }

            // Reload backend wallets after sync
            try {
              const refreshResponse = await fetch(
                `${API_BASE_URL}/api/wallets`,
              );
              if (refreshResponse.ok) {
                const refreshedWallets = await refreshResponse.json();
                setWalletAddresses(refreshedWallets);
                localStorage.setItem(
                  "fundWallets",
                  JSON.stringify(refreshedWallets),
                );
                addDebugInfo(
                  `✅ Refreshed wallet list: ${refreshedWallets.length} wallets`,
                );
              }
            } catch (error) {
              addDebugInfo(
                `⚠️ Could not refresh wallet list: ${error.message}`,
              );
            }
          } else if (backendWallets.length > 0) {
            // Backend has wallets, use them as the source of truth
            setWalletAddresses(backendWallets);
            localStorage.setItem("fundWallets", JSON.stringify(backendWallets));
            addDebugInfo("✅ Using backend wallets as source of truth");
          }
        } else {
          addDebugInfo(`❌ Wallets fetch failed: ${walletsResponse.status}`);
        }

        addDebugInfo("🎉 Portfolio load completed successfully");
      } catch (error) {
        let errorMessage = error.message;

        // Handle specific error types
        if (error.name === "AbortError") {
          errorMessage =
            "Connection timeout - backend taking too long to respond";
        } else if (error.message === "Failed to fetch") {
          errorMessage = "Network error - cannot reach backend server";
        }

        addDebugInfo(
          `❌ Portfolio load error (attempt ${retryCount + 1}/${maxRetries + 1})`,
          errorMessage,
        );

        // Retry with exponential backoff for network errors
        if (
          retryCount < maxRetries &&
          (error.message.includes("Failed to fetch") ||
            error.message.includes("Backend not ready") ||
            error.name === "AbortError" ||
            error.message.includes("Network error") ||
            error.message.includes("TypeError"))
        ) {
          const delay = Math.min(Math.pow(2, retryCount) * 1000, 3000); // Cap at 3s for faster recovery
          addDebugInfo(`🔄 Retrying portfolio load in ${delay / 1000}s...`);
          setTimeout(() => loadPortfolioAndSyncWallets(retryCount + 1), delay);
        } else {
          // Only show error if all retries failed
          if (retryCount >= maxRetries) {
            setUpdateError(
              `Failed to load portfolio after ${maxRetries + 1} attempts: ${errorMessage}`,
            );
          } else {
            setUpdateError(`Failed to load portfolio: ${errorMessage}`);
          }
        }
      }
    };

    // Delay initial load to let backend start up
    const timer = setTimeout(() => loadPortfolioAndSyncWallets(), 3000);
    return () => clearTimeout(timer);
  }, []);

  const updatePortfolio = async () => {
    setIsLoading(true);
    setUpdateError("");
    setUpdateStatus("🔗 Connecting to backend...");

    addDebugInfo(`🔍 [UPDATE] Using API_BASE_URL: ${API_BASE_URL}`);

    try {
      // Step 1: Test backend connection
      setUpdateStatus("🔗 Testing backend connection...");

      // Try the health endpoint first
      const healthResponse = await fetch(`${API_BASE_URL}/health`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });

      if (!healthResponse.ok) {
        throw new Error(
          `Backend health check failed (${healthResponse.status})`,
        );
      }

      const healthData = await healthResponse.json();
      addDebugInfo(`✅ [UPDATE] Backend health check passed`, healthData);

      // Step 2: Trigger portfolio update
      setUpdateStatus("🚀 Starting portfolio update...");
      const response = await fetch(`${API_BASE_URL}/api/portfolio/update`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Update failed (${response.status}): ${errorText}`);
      }

      // Step 3: Wait for processing
      setUpdateStatus("⏳ Processing wallet data...");
      await new Promise((resolve) => setTimeout(resolve, 3000));

      // Step 4: Wait a bit more for backend processing
      setUpdateStatus("⏳ Waiting for backend processing...");
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // Step 5: Fetch updated portfolio data
      setUpdateStatus("📊 Fetching portfolio data...");
      const portfolioResponse = await fetch(`${API_BASE_URL}/api/portfolio`);
      if (!portfolioResponse.ok) {
        const errorText = await portfolioResponse.text();
        throw new Error(
          `Failed to fetch portfolio (${portfolioResponse.status}): ${errorText}`,
        );
      }

      const portfolioData = await portfolioResponse.json();

      // Log the fetched data for debugging
      console.log("Fetched portfolio data:", portfolioData);

      // Step 6: Transform data
      setUpdateStatus("🔄 Processing asset data...");
      const updatedAssets = portfolioData.assets.map((asset) => {
        // Parse NFT metadata if present
        let nftMetadata = null;
        if (asset.nft_metadata) {
          try {
            nftMetadata = JSON.parse(asset.nft_metadata);
          } catch (e) {
            console.warn("Failed to parse NFT metadata:", e);
          }
        }

        // Enhanced NFT detection - check backend flag first
        const isNFT =
          asset.is_nft === true ||
          asset.is_nft === 1 ||
          asset.symbol?.includes("NFT") ||
          asset.name?.includes("Collection") ||
          (asset.balance_formatted &&
            asset.balance_formatted.includes("NFTs")) ||
          (nftMetadata && nftMetadata.token_ids) ||
          false;

        return {
          id: asset.id,
          name: asset.name,
          symbol: asset.symbol,
          balance: asset.balance_formatted || asset.balance,
          priceUSD: asset.price_usd || 0,
          valueUSD: asset.value_usd || 0,
          purchase_price: asset.purchase_price || 0,
          total_invested: asset.total_invested || 0,
          realized_pnl: asset.realized_pnl || 0,
          unrealized_pnl: asset.unrealized_pnl || 0,
          total_return_pct: asset.total_return_pct || 0,
          notes: asset.notes || "",
          isNFT: isNFT,
          floorPrice: asset.floor_price || nftMetadata?.floor_price || 0,
          imageUrl: asset.image_url || nftMetadata?.image_url || null,
          performance24h: asset.price_change_24h || 0,
          tokenIds: nftMetadata?.token_ids || [],
          nftMetadata: asset.nft_metadata || null,
        };
      });

      const newTotalValue = portfolioData.total_value || 0;

      // Generate balance history (simplified - in production you'd fetch from backend)
      const newBalanceHistory =
        newTotalValue > 0
          ? [
              { value: newTotalValue * 0.92 },
              { value: newTotalValue * 0.95 },
              { value: newTotalValue * 0.88 },
              { value: newTotalValue * 0.96 },
              { value: newTotalValue },
            ]
          : [{ value: 0 }];

      console.log(
        `Found ${updatedAssets.length} assets with total value $${newTotalValue}`,
      );

      // Step 7: Fetch individual wallet data
      setUpdateStatus("💼 Updating wallet details...");
      const newWalletData = {};
      let walletCount = 0;

      // First, get updated wallet list from backend
      const walletsListResponse = await fetch(`${API_BASE_URL}/api/wallets`);
      const currentWallets = walletsListResponse.ok
        ? await walletsListResponse.json()
        : walletAddresses;

      for (const wallet of currentWallets) {
        try {
          setUpdateStatus(
            `💼 Processing ${wallet.label} (${++walletCount}/${currentWallets.length})...`,
          );
          const walletResponse = await fetch(
            `${API_BASE_URL}/api/wallets/${wallet.id}/details`,
          );

          if (walletResponse.ok) {
            const walletDetails = await walletResponse.json();
            const walletAssets = walletDetails.assets.map((asset) => {
              // Parse NFT metadata if present
              let nftMetadata = null;
              if (asset.nft_metadata) {
                try {
                  nftMetadata = JSON.parse(asset.nft_metadata);
                } catch (e) {
                  console.warn("Failed to parse NFT metadata:", e);
                }
              }

              // Enhanced NFT detection
              const isNFT =
                asset.is_nft === true ||
                asset.is_nft === 1 ||
                asset.symbol?.includes("NFT") ||
                asset.name?.includes("Collection") ||
                (asset.balance_formatted &&
                  asset.balance_formatted.includes("NFTs")) ||
                (nftMetadata && nftMetadata.token_ids) ||
                false;

              return {
                id: asset.id,
                name: asset.name,
                symbol: asset.symbol,
                balance: asset.balance_formatted || asset.balance,
                priceUSD: asset.price_usd || 0,
                valueUSD: asset.value_usd || 0,
                purchase_price: asset.purchase_price || 0,
                total_invested: asset.total_invested || 0,
                realized_pnl: asset.realized_pnl || 0,
                unrealized_pnl: asset.unrealized_pnl || 0,
                total_return_pct: asset.total_return_pct || 0,
                notes: asset.notes || "",
                isNFT: isNFT,
                floorPrice: asset.floor_price || nftMetadata?.floor_price || 0,
                imageUrl: asset.image_url || nftMetadata?.image_url || null,
                performance24h: asset.price_change_24h || 0,
                tokenIds: nftMetadata?.token_ids || [],
                nftMetadata: asset.nft_metadata || null,
              };
            });

            const walletTotalValue = walletDetails.total_value;

            newWalletData[wallet.id] = {
              assets: walletAssets,
              performance: walletDetails.performance_24h,
              performanceHistory: [
                { value: walletTotalValue * 0.92 },
                { value: walletTotalValue * 0.95 },
                { value: walletTotalValue * 0.88 },
                { value: walletTotalValue * 0.96 },
                { value: walletTotalValue },
              ],
            };
            console.log(
              `✅ Loaded wallet ${wallet.label} with ${walletAssets.length} assets worth $${walletTotalValue.toLocaleString()}`,
            );
          } else if (walletResponse.status === 404) {
            console.warn(
              `⚠️ Wallet ${wallet.label} (ID: ${wallet.id}) not found in backend`,
            );
            setUpdateStatus(
              `⚠️ Wallet ${wallet.label} not found - it may need to be re-added`,
            );
          } else {
            console.error(
              `❌ Error fetching wallet ${wallet.label}: ${walletResponse.status} ${walletResponse.statusText}`,
            );
            setUpdateStatus(
              `❌ Error fetching ${wallet.label}: ${walletResponse.status}`,
            );
          }
        } catch (error) {
          console.error(
            `❌ Network error fetching wallet ${wallet.label}:`,
            error,
          );
          setUpdateStatus(`⚠️ Network error fetching ${wallet.label}`);
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      }

      // Step 8: Save data and force refresh
      setUpdateStatus("💾 Saving data...");
      setWalletData(newWalletData);
      localStorage.setItem("walletData", JSON.stringify(newWalletData));

      // Force update portfolio data
      const newPortfolioData = {
        assets: updatedAssets,
        balanceHistory: newBalanceHistory,
        totalValue: newTotalValue,
        performance24h: portfolioData.performance_24h || 0,
      };
      setPortfolioData(newPortfolioData);

      addDebugInfo("💾 Portfolio data updated after fetch", {
        assetCount: updatedAssets.length,
        totalValue: newTotalValue,
        sampleAsset: updatedAssets[0],
      });

      // Force a fresh load from the API to ensure sync
      setUpdateStatus("🔄 Verifying update...");
      try {
        const verifyResponse = await fetch(`${API_BASE_URL}/api/portfolio`);
        if (verifyResponse.ok) {
          const verifyData = await verifyResponse.json();
          addDebugInfo("✅ Verification successful", {
            backendAssets: verifyData.assets.length,
            backendTotal: verifyData.total_value,
          });
        }
      } catch (verifyError) {
        addDebugInfo("⚠️ Verification failed", verifyError.message);
      }

      // Step 9: Load updated wallet status
      setUpdateStatus("📊 Loading wallet status...");
      try {
        const statusResponse = await fetch(
          `${API_BASE_URL}/api/wallets/status`,
        );
        if (statusResponse.ok) {
          const statusData = await statusResponse.json();
          setWalletStatus(statusData);
          addDebugInfo(
            `📊 Updated wallet status for ${statusData.length} wallets`,
          );
        }
      } catch (error) {
        addDebugInfo("⚠️ Could not refresh wallet status", error.message);
      }

      // Step 10: Complete
      const assetCount = updatedAssets.length;
      const valueFormatted = newTotalValue.toLocaleString();

      // Update the last updated timestamp
      const now = new Date();
      setLastUpdated(now);
      localStorage.setItem("lastUpdated", now.toISOString());

      setUpdateStatus(`✅ Updated ${assetCount} assets • $${valueFormatted}`);
      setTimeout(() => setUpdateStatus(""), 5000);

      addDebugInfo("🎉 Portfolio update completed successfully", {
        totalAssets: assetCount,
        totalValue: newTotalValue,
      });
    } catch (error) {
      console.error("Error updating portfolio:", error);
      console.log(`🔍 [UPDATE ERROR] API_BASE_URL was: ${API_BASE_URL}`);
      console.log(`🔍 [UPDATE ERROR] Error type: ${error.name}`);
      console.log(`🔍 [UPDATE ERROR] Error message: ${error.message}`);

      let errorMessage = "Unknown error occurred";

      if (error.name === "TimeoutError" || error.message.includes("timeout")) {
        errorMessage =
          "⏰ Request timeout - backend is taking too long to respond.";
      } else if (
        error.message.includes("Failed to fetch") ||
        error.message.includes("fetch")
      ) {
        errorMessage = `🔌 Cannot connect to backend server at ${API_BASE_URL}. Backend may be down.`;
      } else if (error.message.includes("CORS")) {
        errorMessage =
          "🚫 CORS error - backend not configured for frontend domain.";
      } else if (error.message.includes("Network")) {
        errorMessage = "🌐 Network error - check your internet connection.";
      } else if (error.message.includes("health check failed")) {
        errorMessage = `❌ Backend health check failed. Backend is not responding properly.`;
      } else {
        errorMessage = `❌ ${error.message}`;
      }

      setUpdateError(errorMessage);
      setUpdateStatus("");
    } finally {
      setIsLoading(false);
    }
  };

  // Calculate metrics with safe fallbacks - include valuable NFTs
  const visibleAssets = (portfolioData.assets || []).filter(
    (asset) => asset && !hiddenAssets.includes(asset.id),
  );

  // Include valuable NFTs from portfolioData.nfts if they exist
  const valuableNFTs = (portfolioData.nfts || []).filter(
    (nft) => nft && nft.floor_price_usd > 1 && !hiddenAssets.includes(nft.id),
  );

  // Combine regular assets and valuable NFTs for calculations
  const allValuedItems = [
    ...visibleAssets,
    ...valuableNFTs.map(nft => ({
      ...nft,
      valueUSD: nft.total_value_usd || nft.floor_price_usd * nft.item_count,
      symbol: nft.symbol,
      name: nft.name,
      isNFT: true
    }))
  ];

  const totalValue = allValuedItems.reduce(
    (sum, item) => sum + (item?.valueUSD || item?.total_value_usd || 0),
    0,
  );

  const topAsset =
    allValuedItems.length > 0
      ? allValuedItems.reduce((prev, current) => {
          const prevValue = prev.valueUSD || prev.total_value_usd || 0;
          const currentValue = current.valueUSD || current.total_value_usd || 0;
          return prevValue > currentValue ? prev : current;
        })
      : null;

  const topAssetWeight = topAsset
    ? (((topAsset.valueUSD || topAsset.total_value_usd || 0) / totalValue) * 100).toFixed(1)
    : 0;

  // Calculate performance vs raised capital
  const raisedCapital = 138000; // Hardcoded raised capital amount
  const performanceVsRaised =
    totalValue > 0 ? ((totalValue - raisedCapital) / raisedCapital) * 100 : 0;
  const performanceSign = performanceVsRaised >= 0 ? "+" : "";
  const performanceChangeType =
    performanceVsRaised >= 0 ? "positive" : "negative";

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Mobile-optimized Header */}
      <div className="border-b border-gray-800 bg-gray-900/50 sticky top-0 z-40">
        <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 sm:space-x-4 min-w-0">
              {/* Removing the icon */}
              <div className="min-w-0 flex-1">
                <h1 className="text-lg sm:text-2xl font-bold truncate">
                  📊 w3e.info
                </h1>
                {/* Status Display */}
                {updateStatus && (
                  <div className="flex items-center space-x-2 mt-1">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                    <p className="text-xs sm:text-sm text-blue-300 truncate">
                      {updateStatus}
                    </p>
                  </div>
                )}
                {updateError && (
                  <div className="flex items-center space-x-2 mt-1">
                    <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                    <p className="text-xs sm:text-sm text-red-300 truncate">
                      Update failed
                    </p>
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center space-x-2 sm:space-x-4 flex-shrink-0">
              {/* Refresh Button with Rebuilt Status System */}
              <div className="relative group">
                <button
                  onClick={updatePortfolio}
                  disabled={isLoading}
                  className={`relative p-2 sm:p-3 rounded-xl transition-all duration-300 overflow-hidden ${
                    isLoading
                      ? "bg-blue-600/30 text-blue-300 cursor-not-allowed ring-2 ring-blue-400/50"
                      : updateError
                        ? "bg-red-600/20 text-red-400 hover:bg-red-600/30 ring-1 ring-red-500/50"
                        : updateStatus && !isLoading
                          ? "bg-green-600/20 text-green-400 hover:bg-green-600/30 ring-1 ring-green-500/50"
                          : "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white shadow-lg hover:shadow-blue-500/25"
                  }`}
                  title={
                    isLoading
                      ? "Updating..."
                      : updateError
                        ? "Update failed"
                        : "Update Portfolio"
                  }
                >
                  {/* Background Animation for Loading */}
                  {isLoading && (
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 to-purple-500/20 animate-pulse"></div>
                  )}

                  {/* Icon */}
                  <svg
                    className={`relative z-10 w-5 h-5 sm:w-6 sm:h-6 transition-transform duration-500 ${
                      isLoading
                        ? "animate-spin"
                        : updateError
                          ? "text-red-400"
                          : updateStatus && !isLoading
                            ? "text-green-400"
                            : "group-hover:rotate-180"
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    {updateError ? (
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    ) : updateStatus && !isLoading ? (
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    ) : (
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    )}
                  </svg>

                  {/* Loading Progress Ring */}
                  {isLoading && (
                    <div className="absolute inset-0 z-20 flex items-center justify-center">
                      <div className="w-8 h-8 border-2 border-transparent border-t-blue-400 rounded-full animate-spin"></div>
                    </div>
                  )}
                </button>

                {/* Enhanced Status Tooltip */}
                <div
                  className={`absolute right-0 top-full mt-2 w-96 bg-gray-900 border-2 rounded-xl shadow-2xl z-50 transition-all duration-300 ${
                    updateStatus || updateError || isLoading
                      ? "opacity-100 scale-100 translate-y-0"
                      : "opacity-0 scale-95 -translate-y-2 pointer-events-none"
                  }`}
                >
                  <div className="p-4">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-4">
                      <h4 className="text-base font-bold text-white flex items-center space-x-2">
                        <span>Portfolio Update</span>
                        {isLoading && (
                          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                        )}
                        {updateError && (
                          <div className="w-2 h-2 bg-red-400 rounded-full"></div>
                        )}
                        {updateStatus && !isLoading && !updateError && (
                          <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                        )}
                      </h4>
                    </div>

                    {/* Loading Status */}
                    {isLoading && updateStatus && (
                      <div className="mb-4">
                        <div className="flex items-center space-x-3 mb-3">
                          <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
                          <p className="text-sm text-blue-300 flex-1">
                            {updateStatus}
                          </p>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full animate-pulse transition-all duration-1000"
                            style={{ width: "75%" }}
                          ></div>
                        </div>
                      </div>
                    )}

                    {/* Success Status */}
                    {updateStatus && !isLoading && !updateError && (
                      <div className="mb-4 p-3 bg-green-900/20 border border-green-700/50 rounded-lg">
                        <div className="flex items-center space-x-2 mb-2">
                          <svg
                            className="w-4 h-4 text-green-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                          <p className="text-sm text-green-300 font-medium">
                            Update Complete!
                          </p>
                        </div>
                        <p className="text-xs text-green-400">{updateStatus}</p>
                      </div>
                    )}

                    {/* Error Status */}
                    {updateError && (
                      <div className="mb-4 p-3 bg-red-900/20 border border-red-700/50 rounded-lg">
                        <div className="flex items-center space-x-2 mb-2">
                          <svg
                            className="w-4 h-4 text-red-400"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <p className="text-sm text-red-300 font-medium">
                            Update Failed
                          </p>
                        </div>
                        <p className="text-xs text-red-400 mb-3">
                          {updateError}
                        </p>

                        <div className="bg-red-900/30 rounded p-2">
                          <p className="text-xs font-medium text-red-300 mb-1">
                            🔧 Troubleshooting:
                          </p>
                          <ul className="text-xs text-red-400 space-y-1">
                            <li>• Check if backend is running on port 8000</li>
                            <li>• Verify environment variables are set</li>
                            <li>• Try refreshing the page</li>
                          </ul>
                        </div>
                      </div>
                    )}

                    {/* Footer */}
                    <div className="text-xs text-gray-500 text-center">
                      {lastUpdated
                        ? `Last updated: ${lastUpdated.toLocaleTimeString()}`
                        : "Never updated"}
                    </div>
                  </div>
                </div>
              </div>

              <button
                onClick={() => setShowSettings(true)}
                className="text-gray-400 hover:text-white transition-colors p-1 sm:p-2"
                title="Settings"
              >
                <svg
                  className="w-4 h-4 sm:w-5 sm:h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 sm:px-6 py-4 sm:py-6">
        {/* Key Metrics - Mobile responsive grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-6 sm:mb-8">
          <MetricCard
            title="Total Value"
            value={`$${totalValue.toLocaleString()}`}
            change={
              <div className="flex items-center space-x-2">
                <div
                  className={`w-2 h-2 rounded-full ${getLiveStatus().dot}`}
                ></div>
                <span className={getLiveStatus().color}>
                  {getLiveStatus().text}
                </span>
              </div>
            }
            changeType="white"
          />

          <MetricCard
            title="Performance"
            value={
              <span
                className={
                  performanceVsRaised >= 0 ? "text-green-400" : "text-red-400"
                }
              >
                {performanceSign}
                {performanceVsRaised.toFixed(1)}%
              </span>
            }
            change="Since inception"
            changeType="white"
          />

          <MetricCard
            title="Assets"
            value={allValuedItems.length}
            change="Active positions"
            changeType="white"
          />

          <MetricCard
            title="Top Asset"
            value={topAsset?.symbol || "N/A"}
            change={`${topAssetWeight}% of portfolio`}
            changeType="white"
          />
        </div>

        {/* Chart Section - Temporarily hidden until properly implemented */}
        {false && (
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6 mb-6 sm:mb-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 sm:mb-6 space-y-3 sm:space-y-0">
              <h3 className="text-base sm:text-lg font-semibold text-white">
                Portfolio Performance
              </h3>
              <div className="flex space-x-2 overflow-x-auto">
                <button className="px-3 py-1 text-xs bg-purple-600 text-white rounded-md whitespace-nowrap">
                  7D
                </button>
                <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600 whitespace-nowrap">
                  30D
                </button>
                <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600 whitespace-nowrap">
                  90D
                </button>
                <button className="px-3 py-1 text-xs bg-gray-700 text-gray-300 rounded-md hover:bg-gray-600 whitespace-nowrap">
                  1Y
                </button>
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
              title="📊 Returns Analysis"
              description="View detailed performance metrics and top performers"
              buttonText="View Returns"
              onAction={() => setShowReturnsModal(true)}
              variant="primary"
            />

            <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6">
              <h3 className="text-base sm:text-lg font-semibold mb-2 text-white">
                Generate Reports
              </h3>
              <p className="text-sm text-gray-400 mb-4">
                Export performance reports
              </p>
              <ReportGenerator
                portfolioData={{ ...portfolioData, totalValue }}
              />
            </div>
          </div>
        )}

        {/* Wallet Management Section */}
        {isEditor && (
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-4 sm:p-6 mb-6 sm:mb-8">
            <h3 className="text-base sm:text-lg font-semibold mb-4 text-white">
              Fund Wallets
            </h3>

            {/* Current Wallets with Status */}
            <div className="space-y-3 mb-6">
              {walletAddresses.map((wallet) => {
                const status = walletStatus.find(
                  (s) => s.wallet_id === wallet.id,
                );
                const statusColor =
                  status?.status === "success"
                    ? "bg-green-500"
                    : status?.status === "error"
                      ? "bg-red-500"
                      : status?.status === "timeout"
                        ? "bg-yellow-500"
                        : "bg-gray-500";
                const statusText =
                  status?.status === "success"
                    ? "✅"
                    : status?.status === "error"
                      ? "❌"
                      : status?.status === "timeout"
                        ? "⏰"
                        : "❓";

                return (
                  <div
                    key={wallet.id}
                    className="p-3 bg-gray-800 rounded-lg border border-gray-700"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3 min-w-0 flex-1">
                        <div className="w-8 h-8 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                          <span className="text-white font-bold text-xs">
                            {wallet.network}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center space-x-2">
                            <p className="text-white font-medium text-sm">
                              {wallet.label}
                            </p>
                            <span className="text-xs">{statusText}</span>
                            <div
                              className={`w-2 h-2 rounded-full ${statusColor} flex-shrink-0`}
                            ></div>
                          </div>
                          <p className="text-gray-400 text-xs font-mono break-all">
                            {wallet.address}
                          </p>
                        </div>
                      </div>
                      <button
                        onClick={() => removeWallet(wallet.id)}
                        className="text-red-400 hover:text-red-300 p-1 ml-2 flex-shrink-0"
                        title="Remove wallet"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                          />
                        </svg>
                      </button>
                    </div>

                    {/* Wallet Status Details */}
                    {status && (
                      <div className="grid grid-cols-3 gap-2 text-xs text-gray-400 mt-2 pt-2 border-t border-gray-700">
                        <div>
                          <span className="block">Assets</span>
                          <span className="text-white">
                            {status.assets_found || 0}
                          </span>
                        </div>
                        <div>
                          <span className="block">Value</span>
                          <span className="text-white">
                            ${(status.total_value || 0).toLocaleString()}
                          </span>
                        </div>
                        <div>
                          <span className="block">Status</span>
                          <span
                            className={`${
                              status.status === "success"
                                ? "text-green-400"
                                : status.status === "error"
                                  ? "text-red-400"
                                  : status.status === "timeout"
                                    ? "text-yellow-400"
                                    : "text-gray-400"
                            }`}
                          >
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
              <h4 className="text-sm font-medium text-gray-300 mb-3">
                Add New Wallet
              </h4>
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
                  className="col-span-1 sm:col-span-1 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors font-medium text-sm"
                >
                  Add Wallet
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Current Positions Grid - Mobile responsive */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <div>
              <h3 className="text-base sm:text-lg font-semibold text-white">
                Current Positions
              </h3>
              <p className="text-xs sm:text-sm text-gray-400">
                {allValuedItems.length} positions • $
                {totalValue.toLocaleString()}
              </p>
            </div>
          </div>

          {allValuedItems.length === 0 ? (
            <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 sm:p-8 text-center">
              <div className="mb-4">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-800 rounded-full flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2M4 13h2m13-8l-4 4m0 0l-4-4m4 4V3"
                    />
                  </svg>
                </div>
              </div>
              <h4 className="text-lg sm:text-xl font-semibold text-white mb-2">
                No Token Data Found
              </h4>
              <p className="text-sm text-gray-400 mb-6 max-w-md mx-auto">
                Your portfolio appears to be empty. Click the "Update Database"
                button to fetch the latest wallet balances and asset data from
                your configured wallets.
              </p>
              <button className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors font-medium">
                {isLoading ? <LoadingSpinner /> : "🔄 Update Database"}
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {/* Regular Assets */}
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
              
              {/* Valuable NFTs */}
              {valuableNFTs.map((nft) => (
                <AssetCard
                  key={nft.id}
                  asset={{
                    id: nft.id,
                    symbol: nft.symbol,
                    name: nft.name,
                    balance: `${nft.item_count} NFTs`,
                    priceUSD: nft.floor_price_usd,
                    valueUSD: nft.total_value_usd || nft.floor_price_usd * nft.item_count,
                    purchase_price: nft.purchase_price || 0,
                    total_invested: nft.total_invested || 0,
                    realized_pnl: nft.realized_pnl || 0,
                    unrealized_pnl: nft.unrealized_pnl || 0,
                    total_return_pct: nft.total_return_pct || 0,
                    notes: nft.notes || "",
                    isNFT: true,
                    floorPrice: nft.floor_price_usd,
                    imageUrl: nft.image_url,
                    tokenIds: nft.token_ids || [],
                  }}
                  onClick={() => setSelectedAsset({
                    id: nft.id,
                    symbol: nft.symbol,
                    name: nft.name,
                    balance: `${nft.item_count} NFTs`,
                    priceUSD: nft.floor_price_usd,
                    valueUSD: nft.total_value_usd || nft.floor_price_usd * nft.item_count,
                    purchase_price: nft.purchase_price || 0,
                    total_invested: nft.total_invested || 0,
                    realized_pnl: nft.realized_pnl || 0,
                    unrealized_pnl: nft.unrealized_pnl || 0,
                    total_return_pct: nft.total_return_pct || 0,
                    notes: nft.notes || "",
                    isNFT: true,
                    floorPrice: nft.floor_price_usd,
                    imageUrl: nft.image_url,
                    tokenIds: nft.token_ids || [],
                  })}
                  onHide={() => toggleHiddenAsset({
                    id: nft.id,
                    symbol: nft.symbol,
                    name: nft.name
                  })}
                  isEditor={isEditor}
                  totalValue={totalValue}
                />
              ))}
            </div>
          )}
        </div>

        {/* Wallets Section */}
        <div className="mb-6 sm:mb-8">
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <div>
              <h3 className="text-base sm:text-lg font-semibold text-white">
                Fund Wallets
              </h3>
              <p className="text-xs sm:text-sm text-gray-400">
                {walletAddresses.length} wallets •{" "}
                {Object.keys(walletData).length} with data
              </p>
            </div>
          </div>

          {walletAddresses.length === 0 ? (
            <div className="bg-gray-900 border border-gray-700 rounded-xl p-6 sm:p-8 text-center">
              <div className="mb-4">
                <div className="w-16 h-16 mx-auto mb-4 bg-gray-800 rounded-full flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-gray-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
                    />
                  </svg>
                </div>
              </div>
              <h4 className="text-lg sm:text-xl font-semibold text-white mb-2">
                No Wallets Configured
              </h4>
              <p className="text-sm text-gray-400 mb-6 max-w-md mx-auto">
                Add wallet addresses to start tracking individual wallet
                performance and asset breakdowns.
              </p>
              {isEditor && (
                <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium">
                  🏦 Add First Wallet
                </button>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
              {walletAddresses.map((wallet) => {
                // Check if wallet has status info to determine if there's an error
                const status = walletStatus.find(
                  (s) => s.wallet_id === wallet.id,
                );
                const hasData = walletData[wallet.id];
                const hasError =
                  status?.status === "error" ||
                  (!hasData && wallet.network === "SOL");

                return (
                  <WalletCard
                    key={wallet.id}
                    wallet={wallet}
                    onClick={() => setSelectedWallet(wallet)}
                    walletData={
                      walletData[wallet.id] || {
                        assets: [],
                        performance: 0,
                        hasError,
                      }
                    }
                    assets={portfolioData.assets}
                    totalValue={portfolioData.totalValue}
                    performance={portfolioData.performance24h || 0}
                  />
                );
              })}
            </div>
          )}
        </div>

        {/* Hidden Assets */}
        {hiddenAssets.length > 0 && isEditor && (
          <div className="mb-6 sm:mb-8">
            <h3 className="text-base sm:text-lg font-semibold text-white mb-4">
              Hidden Assets
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {portfolioData.assets
                .filter((asset) => hiddenAssets.includes(asset.id))
                .map((asset) => (
                  <div
                    key={asset.id}
                    className="bg-gray-800 border border-gray-600 rounded-lg p-4 opacity-60"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs font-bold">
                            {asset.symbol.slice(0, 2)}
                          </span>
                        </div>
                        <span className="text-white text-sm">{asset.name}</span>
                      </div>
                      <button
                        onClick={() => toggleHiddenAsset(asset)}
                        className="text-xs bg-green-600/20 text-green-400 px-2 py-1 rounded-md hover:bg-green-600/30 transition-colors border border-green-600/30"
                      >
                        Show
                      </button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Asset Modal */}
        {selectedAsset && (
          <AssetModal
            asset={selectedAsset}
            onClose={() => setSelectedAsset(null)}
            onUpdateNotes={updateNotes}
            onUpdatePurchasePrice={updatePurchasePrice}
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

        {/* Returns Analysis Modal */}
        <ReturnsModal
          isOpen={showReturnsModal}
          onClose={() => setShowReturnsModal(false)}
          portfolioData={portfolioData}
        />
      </div>
    </div>
  );
};

export default App;
