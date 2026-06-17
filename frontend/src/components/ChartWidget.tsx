/**
 * ChartWidget - K线图表组件
 *
 * 基于lightweight-charts v4，提供：
 * - K线蜡烛图（支持缩放、拖拽、十字光标）
 * - 太极中心点标记叠加层
 * - 斐波那契回撤/扩展水平线
 * - 波浪标签
 * - 实时K线更新（通过update方法追加）
 */

import React, { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  CrosshairMode,
  LineStyle,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
  type CandlestickData,
  type SeriesMarker,
  type Time,
  type IPriceLine,
} from "lightweight-charts";
import type { Bar } from "@/types";

// ============================================================
// 类型定义
// ============================================================

/** 太极中心点标记数据 */
export interface TaijiMarker {
  time: string;
  price: number;
  isTop: boolean;
  text?: string;
}

/** 斐波那契水平线数据 */
export interface FibLevel {
  price: number;
  level: number;
  color?: string;
}

/** 波浪标签数据 */
export interface WaveLabel {
  time: string;
  label: string;
  isImpulse: boolean;
}

/** ChartWidget组件属性 */
export interface ChartWidgetProps {
  /** K线数据 */
  bars: Bar[];
  /** 太极中心点标记列表 */
  taijiMarkers?: TaijiMarker[];
  /** 斐波那契水平线列表 */
  fibLevels?: FibLevel[];
  /** 波浪标签列表 */
  waveLabels?: WaveLabel[];
  /** 图表高度（默认60vh） */
  height?: number | string;
  /** 加载状态 */
  loading?: boolean;
}

// ============================================================
// 工具函数
// ============================================================

/**
 * 将ISO时间字符串转换为UTCTimestamp
 */
function toUTCTimestamp(iso: string): UTCTimestamp {
  return Math.floor(new Date(iso).getTime() / 1000) as UTCTimestamp;
}

/**
 * 将Bar数组转换为lightweight-charts所需的CandlestickData格式
 */
function toCandlestickData(bars: Bar[]): CandlestickData<Time>[] {
  return bars
    .map((bar) => ({
      time: toUTCTimestamp(bar.timestamp),
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    }))
    .sort((a, b) => (a.time as number) - (b.time as number));
}

/**
 * 将太极标记转换为lightweight-charts的SeriesMarker格式
 */
function toSeriesMarkers(markers: TaijiMarker[]): SeriesMarker<Time>[] {
  return markers
    .map((marker) => ({
      time: toUTCTimestamp(marker.time),
      position: marker.isTop ? ("aboveBar" as const) : ("belowBar" as const),
      color: marker.isTop ? "#26a69a" : "#ef5350",
      shape: marker.isTop ? ("arrowDown" as const) : ("arrowUp" as const),
      text: marker.text ?? (marker.isTop ? "▼太极顶" : "▲太极底"),
    }))
    .sort((a, b) => (a.time as number) - (b.time as number));
}

// ============================================================
// 组件实现
// ============================================================

/**
 * ChartWidget - K线图表组件
 *
 * 使用lightweight-charts v4创建专业K线图，支持：
 * - 蜡烛图主序列
 * - 太极中心点标记
 * - 斐波那契水平线
 * - 波浪标签（通过marker text实现）
 * - 实时数据更新
 */
const ChartWidget: React.FC<ChartWidgetProps> = ({
  bars,
  taijiMarkers = [],
  fibLevels = [],
  waveLabels = [],
  height = "60vh",
  loading = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
  const priceLinesRef = useRef<IPriceLine[]>([]);

  // 初始化图表
  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: typeof height === "number" ? height : 600,
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#333",
        fontFamily: "Roboto, sans-serif",
      },
      grid: {
        vertLines: { color: "rgba(197, 203, 206, 0.3)" },
        horzLines: { color: "rgba(197, 203, 206, 0.3)" },
      },
      crosshair: {
        mode: CrosshairMode.Normal,
      },
      rightPriceScale: {
        borderColor: "rgba(197, 203, 206, 1)",
      },
      timeScale: {
        borderColor: "rgba(197, 203, 206, 1)",
        timeVisible: true,
        secondsVisible: false,
      },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: "#ef5350",
      downColor: "#26a69a",
      borderUpColor: "#ef5350",
      borderDownColor: "#26a69a",
      wickUpColor: "#ef5350",
      wickDownColor: "#26a69a",
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    // 响应式调整大小
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const newWidth = entry.contentRect.width;
        chart.applyOptions({ width: newWidth });
      }
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
      candleSeriesRef.current = null;
      priceLinesRef.current = [];
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 更新K线数据
  useEffect(() => {
    if (!candleSeriesRef.current || bars.length === 0) return;

    const candleData = toCandlestickData(bars);
    candleSeriesRef.current.setData(candleData);

    // 自动调整可见范围
    if (chartRef.current && candleData.length > 0) {
      chartRef.current.timeScale().fitContent();
    }
  }, [bars]);

  // 更新太极标记 + 波浪标签
  useEffect(() => {
    if (!candleSeriesRef.current) return;

    const allMarkers: SeriesMarker<Time>[] = [];

    // 太极中心点标记
    allMarkers.push(...toSeriesMarkers(taijiMarkers));

    // 波浪标签（使用marker text显示）
    for (const wave of waveLabels) {
      allMarkers.push({
        time: toUTCTimestamp(wave.time),
        position: "belowBar" as const,
        color: wave.isImpulse ? "#2196F3" : "#FF9800",
        shape: "circle" as const,
        text: wave.label,
        size: 1,
      });
    }

    // 按时间排序
    allMarkers.sort((a, b) => (a.time as number) - (b.time as number));

    // lightweight-charts v4: setMarkers
    candleSeriesRef.current.setMarkers(allMarkers);
  }, [taijiMarkers, waveLabels]);

  // 更新斐波那契水平线
  useEffect(() => {
    if (!candleSeriesRef.current) return;

    // 清除旧的价格线
    for (const line of priceLinesRef.current) {
      candleSeriesRef.current.removePriceLine(line);
    }
    priceLinesRef.current = [];

    // 添加新的斐波那契水平线
    for (const level of fibLevels) {
      const color = level.color ?? getFibColor(level.level);
      const line = candleSeriesRef.current.createPriceLine({
        price: level.price,
        color,
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: `Fib ${level.level.toFixed(3)}`,
      });
      priceLinesRef.current.push(line);
    }
  }, [fibLevels]);

  /**
   * 根据斐波那契比例返回对应颜色
   */
  function getFibColor(level: number): string {
    if (level >= 0.618) return "#F44336";
    if (level >= 0.5) return "#FF9800";
    if (level >= 0.382) return "#FFC107";
    return "#4CAF50";
  }

  return (
    <div className="relative w-full" style={{ height }}>
      {loading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/60">
          <div className="text-gray-500">加载K线数据中...</div>
        </div>
      )}
      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
};

export default ChartWidget;
