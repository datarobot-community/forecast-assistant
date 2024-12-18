// TODO fix types
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-nocheck
import {
  useContext,
  useRef,
  useState,
  useMemo,
  useEffect,
  useLayoutEffect,
  useCallback,
} from "react";
import { format as d3Format } from "d3";
import { defaultStyles, useTooltip, TooltipWithBounds } from "@visx/tooltip";
import { scaleTime, scaleLinear } from "@visx/scale";
import { Group } from "@visx/group";
import { LinePath, Line, Bar } from "@visx/shape";
import { AxisLeft, AxisBottom } from "@visx/axis";
import { GridRows } from "@visx/grid";
import { localPoint } from "@visx/event";
import { Brush } from "@visx/brush";
import { BrushHandleRenderProps } from "@visx/brush/lib/BrushHandle";
import { Bounds } from "@visx/brush/lib/types";
import useMeasure from "react-use-measure";
import { bisector } from "d3-array";
import twColors from "tailwindcss/colors";
import LoadingBackdrop from "~/components/ui-custom/LoadingBackdrop";
import {
  AppStateContext,
  type ScoringData,
  type ForecastData,
  WhatIfScenario,
} from "~/state/AppState";
import { momentDate } from "~/helpers";

const margin = {
  top: 30,
  right: 60,
  bottom: 140,
  left: 60,
};

const WhatIfScenariosLineChart = () => {
  const brushRef = useRef(null);
  const [ref, bounds] = useMeasure();
  const {
    showTooltip,
    hideTooltip,
    tooltipData,
    tooltipLeft = 0,
    tooltipTop = 0,
  } = useTooltip<ScoringData | ForecastData>();

  const {
    appSettings,
    scoringData,
    forecastData: originalForecast,
    doesDateContainTime,
    whatIfScenarios,
    activeWhatIfScenarioId,
  } = useContext(AppStateContext);
  const {
    datetime_partition_column: dateColumn,
    target: targetColumn,
    graph_y_axis,
  } = appSettings;

  const {
    name: scenarioName,
    forecastData: scenarioForecast,
    isLoadingForecastData,
  } = useMemo(
    () =>
      whatIfScenarios.find((s) => s.id === activeWhatIfScenarioId) ||
      ({} as WhatIfScenario),
    [whatIfScenarios, activeWhatIfScenarioId]
  );

  const getXValue = (d: ScoringData) =>
    d?.[dateColumn] ? momentDate(d[dateColumn]) : null;

  const getYValue = useCallback(
    (d: ScoringData) => d[targetColumn],
    [targetColumn]
  );

  const getForecastXValue = useCallback(
    (d: ForecastData) => (d?.timestamp ? momentDate(d.timestamp) : null),
    []
  );

  const getForecastYValue = useCallback((d: ForecastData) => d.prediction, []);

  const scoringBisectDate = useMemo(
    () => bisector<ScoringData, Date>((d) => momentDate(d[dateColumn])).left,
    [dateColumn]
  );

  const forecastBisectDate = useMemo(
    () => bisector<ForecastData, Date>((d) => momentDate(d.timestamp)).left,
    []
  );

  const getMaxDateScoringAndForecast = useCallback(
    (scoringData: ScoringData[], forecastData: ForecastData[]) => {
      const scoringMaxDate = getXValue(
        scoringData[scoringData.length - 1]
      ) as Date;
      const forecastMaxDate = getForecastXValue(
        forecastData[forecastData.length - 1]
      ) as Date;

      return scoringMaxDate > forecastMaxDate
        ? scoringMaxDate
        : forecastMaxDate;
    },
    [getXValue, getForecastXValue]
  );

  const scoringDataWithoutNullValues = useMemo(
    () => scoringData.filter((d) => d[targetColumn] !== null),
    [scoringData]
  );

  const [filteredScoringData, setFilteredScoringData] = useState<ScoringData[]>(
    scoringDataWithoutNullValues
  );
  const [filteredOriginalForecast, setFilteredOriginalForecast] =
    useState<ForecastData[]>(originalForecast);
  const [filteredScenarioForecast, setFilteredScenarioForecast] = useState<
    ForecastData[]
  >([]);

  const { xMax, yMax } = useMemo(() => {
    const width = bounds.width || 200;
    const height = bounds.height || 200;

    const xMax = width - margin.left - margin.right;
    const yMax = height - margin.top - margin.bottom;

    return { xMax, yMax };
  }, [bounds]);

  const yBrushMax = 50;

  const initialDateRange: [Date, Date] = useMemo(() => {
    return [
      getXValue(scoringDataWithoutNullValues[0]) as Date,
      getMaxDateScoringAndForecast(
        scoringDataWithoutNullValues,
        originalForecast
      ),
    ];
  }, [scoringDataWithoutNullValues, originalForecast]);

  const [selectedDateRange, setSelectedDateRange] = useState<[Date, Date]>(
    initialDateRange as [Date, Date]
  );
  const xScale = scaleTime({
    domain: selectedDateRange,
    range: [0, xMax],
  });

  const yScale = useMemo(() => {
    const concData = [
      ...filteredScoringData.map(getYValue),
      ...filteredOriginalForecast.map(getForecastYValue),
      ...(filteredScenarioForecast || []).map(getForecastYValue),
    ];
    return scaleLinear({
      domain: [Math.min(...concData), Math.max(...concData)],
      range: [yMax, 0],
    });
  }, [
    filteredScoringData,
    filteredOriginalForecast,
    filteredScenarioForecast,
    yMax,
  ]);

  const brushXScale = scaleTime({
    domain: initialDateRange,
    range: [0, xMax],
  });

  const brushYScale = useMemo(() => {
    const concData = [
      ...scoringDataWithoutNullValues.map(getYValue),
      ...originalForecast.map(getForecastYValue),
    ];

    return scaleLinear({
      domain: [Math.min(...concData), Math.max(...concData)],
      range: [yBrushMax, 0],
    });
  }, [scoringDataWithoutNullValues, originalForecast, yBrushMax]);

  const initialBrushPosition = {
    start: {
      x: brushXScale(selectedDateRange[0]),
    },
    end: {
      x: brushXScale(selectedDateRange[1]),
    },
  };

  const handleTooltipMouseMove = useCallback(
    (
      event: React.TouchEvent<SVGRectElement> | React.MouseEvent<SVGRectElement>
    ) => {
      let { x, y } = localPoint(event) || { x: 0, y: 0 };

      x -= margin.left;
      y -= margin.top;
      const x0 = xScale.invert(x);

      // Find closest data points for both scoringData and forecastData
      const scoringIndex = scoringBisectDate(filteredScoringData, x0, 1);
      const forecastIndex = forecastBisectDate(filteredOriginalForecast, x0, 1);

      const scoringDataPoint = filteredScoringData[scoringIndex - 1];
      const scoringDataPointNext = filteredScoringData[scoringIndex];

      const forecastDataPoint = filteredOriginalForecast[forecastIndex - 1];
      const forecastDataPointNext = filteredOriginalForecast[forecastIndex];

      // Determine the closest data point for scoringData
      let closestScoringDataPoint = scoringDataPoint;
      if (scoringDataPointNext && getXValue(scoringDataPointNext)) {
        closestScoringDataPoint =
          x0.valueOf() - getXValue(scoringDataPoint).valueOf() >
          getXValue(scoringDataPointNext).valueOf() - x0.valueOf()
            ? scoringDataPointNext
            : scoringDataPoint;
      }

      // Determine the closest data point for forecastData
      let closestForecastDataPoint = forecastDataPoint;
      if (forecastDataPointNext && getForecastXValue(forecastDataPointNext)) {
        closestForecastDataPoint =
          x0.valueOf() - getForecastXValue(forecastDataPoint).valueOf() >
          getForecastXValue(forecastDataPointNext).valueOf() - x0.valueOf()
            ? forecastDataPointNext
            : forecastDataPoint;
      }

      // Determine which data point is the closest to the cursor position
      let closestDataPoint = closestScoringDataPoint;
      if (closestScoringDataPoint && closestForecastDataPoint) {
        closestDataPoint =
          Math.abs(
            x0.valueOf() - getXValue(closestScoringDataPoint).valueOf()
          ) <
          Math.abs(
            x0.valueOf() - getForecastXValue(closestForecastDataPoint).valueOf()
          )
            ? closestScoringDataPoint
            : closestForecastDataPoint;
      } else if (closestForecastDataPoint) {
        closestDataPoint = closestForecastDataPoint;
      }

      showTooltip({
        tooltipData: closestDataPoint,
        tooltipLeft: x,
        tooltipTop: y,
      });
    },
    [
      xScale,
      showTooltip,
      getXValue,
      getForecastXValue,
      filteredScoringData,
      filteredOriginalForecast,
    ]
  );

  const handleBrushChange = (domain: Bounds | null) => {
    if (!domain) return;
    const { x0, x1 } = domain;
    const xMinBrush = x0 > x1 ? x1 : x0;
    const xMaxBrush = x0 > x1 ? x0 : x1;

    if (xMaxBrush - xMinBrush < 10) return;

    const tempFilteredScoringData = scoringDataWithoutNullValues.filter(
      (d) => getXValue(d) >= xMinBrush && getXValue(d) <= xMaxBrush
    );
    setFilteredScoringData(tempFilteredScoringData);

    const tempFilteredOriginalForecast = originalForecast.filter(
      (d) =>
        getForecastXValue(d) >= xMinBrush && getForecastXValue(d) <= xMaxBrush
    );
    setFilteredOriginalForecast(tempFilteredOriginalForecast);

    const tempFilteredScenarioForecast = (scenarioForecast || []).filter(
      (d) =>
        getForecastXValue(d) >= xMinBrush && getForecastXValue(d) <= xMaxBrush
    );
    setFilteredScenarioForecast(tempFilteredScenarioForecast);

    setSelectedDateRange([
      (getXValue(tempFilteredScoringData[0]) ||
        getForecastXValue(tempFilteredOriginalForecast[0])) as Date,
      getMaxDateScoringAndForecast(
        tempFilteredScoringData,
        tempFilteredOriginalForecast
      ) as Date,
    ]);
  };

  useLayoutEffect(() => {
    setSelectedDateRange([
      (getXValue(filteredScoringData[0]) ||
        getForecastXValue(filteredOriginalForecast[0])) as Date,
      getMaxDateScoringAndForecast(
        filteredScoringData,
        filteredOriginalForecast
      ) as Date,
    ]);
  }, [filteredScoringData, filteredOriginalForecast]);

  useEffect(() => {
    const { start, end } = (
      (brushRef?.current || {
        state: {
          start: {
            x: 0,
          },
          end: {
            x: 0,
          },
        },
      }) as { state: { start: { x: number }; end: { x: number } } }
    ).state;

    const xMinBrush = start.x < end.x ? start.x : end.x;
    const xMaxBrush = start.x < end.x ? end.x : start.x;

    if ((xMinBrush == 0 && xMaxBrush == 0) || xMinBrush < 0 || xMaxBrush < 0) {
      setFilteredScoringData(scoringDataWithoutNullValues);
      setFilteredOriginalForecast(originalForecast);
      setFilteredScenarioForecast(scenarioForecast || []);
      return;
    }

    const tempFilteredScoringData = scoringDataWithoutNullValues.filter(
      (d) =>
        getXValue(d) >= brushXScale.invert(xMinBrush) &&
        getXValue(d) <= brushXScale.invert(xMaxBrush)
    );
    setFilteredScoringData(tempFilteredScoringData);

    const tempFilteredOriginalForecast = originalForecast.filter(
      (d) =>
        getForecastXValue(d) >= brushXScale.invert(xMinBrush) &&
        getForecastXValue(d) <= brushXScale.invert(xMaxBrush)
    );
    setFilteredOriginalForecast(tempFilteredOriginalForecast);

    const tempFilteredScenarioForecast = (scenarioForecast || []).filter(
      (d) =>
        getForecastXValue(d) >= brushXScale.invert(xMinBrush) &&
        getForecastXValue(d) <= brushXScale.invert(xMaxBrush)
    );
    setFilteredScenarioForecast(tempFilteredScenarioForecast);

    setSelectedDateRange([
      (getXValue(tempFilteredScoringData[0]) ||
        getForecastXValue(tempFilteredOriginalForecast[0])) as Date,
      getMaxDateScoringAndForecast(
        tempFilteredScoringData,
        originalForecast
      ) as Date,
    ]);
  }, [
    scoringDataWithoutNullValues,
    originalForecast,
    scenarioForecast,
    brushRef.current,
  ]);

  return (
    <div className='relative h-[550px]'>
      <ChartLegend scenarioName={scenarioName} />
      <svg ref={ref} width='100%' height='520px'>
        <Group left={margin.left} top={margin.top}>
          <GridRows
            scale={yScale}
            width={xMax}
            height={yMax}
            stroke={twColors.gray[700]}
          />
          <AxisLeft
            scale={yScale}
            stroke={twColors.gray[500]}
            tickStroke={twColors.gray[500]}
            tickLabelProps={{ fill: twColors.gray[400] }}
            label={graph_y_axis}
            labelProps={{ fill: twColors.gray[200], fontSize: 12 }}
            tickFormat={(value) => d3Format(".2s")(value)}
          />
          <AxisBottom
            scale={xScale}
            top={yMax}
            stroke={twColors.gray[500]}
            tickStroke={twColors.gray[500]}
            tickLabelProps={{
              fill: twColors.gray[400],
              fontSize: 12,
            }}
            label='Date'
            labelProps={{ fill: twColors.gray[200], fontSize: 12 }}
            numTicks={5}
            tickFormat={(date) => {
              const day = date.getDate().toString().padStart(2, "0");
              const month = (date.getMonth() + 1).toString().padStart(2, "0");
              const year = date.getFullYear();
              return `${day}/${month}/${year}`;
            }}
          />
          <LinePath
            data={filteredScoringData}
            x={(d) => xScale(getXValue(d))}
            y={(d) => yScale(getYValue(d))}
            stroke='hsl(var(--primary))'
            strokeWidth={1.5}
          />
          <LinePath
            data={filteredOriginalForecast}
            x={(d) => xScale(getForecastXValue(d))}
            y={(d) => yScale(getForecastYValue(d))}
            stroke='hsl(var(--primary))'
            strokeWidth={3}
          />
          <LinePath
            data={filteredScenarioForecast}
            x={(d) => xScale(getForecastXValue(d))}
            y={(d) => yScale(getForecastYValue(d))}
            stroke='#589FA3'
            strokeWidth={3}
          />
        </Group>
        <Group left={margin.left} top={margin.top}>
          <Bar
            width={xMax + 1}
            height={yMax}
            fill='transparent'
            onMouseMove={handleTooltipMouseMove}
            onMouseLeave={() => {
              hideTooltip();
            }}
          />
        </Group>
        {tooltipData ? (
          <Group left={margin.left} top={margin.top}>
            <Line
              from={{ x: tooltipLeft, y: 0 }}
              to={{ x: tooltipLeft, y: yMax }}
              stroke='white'
              strokeWidth={2}
              opacity={0.2}
              pointerEvents='none'
            />
          </Group>
        ) : null}
        <Group left={margin.left} top={yMax + margin.bottom - yBrushMax}>
          <LinePath
            data={scoringDataWithoutNullValues}
            x={(d) => brushXScale(getXValue(d))}
            y={(d) => brushYScale(getYValue(d))}
            stroke='hsl(var(--primary))'
          />
          <LinePath
            data={originalForecast}
            x={(d) => brushXScale(getForecastXValue(d))}
            y={(d) => brushYScale(getForecastYValue(d))}
            stroke='hsl(var(--primary))'
          />
          <Brush
            xScale={brushXScale}
            yScale={brushYScale}
            width={xMax}
            height={yBrushMax}
            margin={{ top: 10, bottom: 15, left: 50, right: 20 }}
            handleSize={8}
            innerRef={brushRef}
            resizeTriggerAreas={["left"]}
            brushDirection='horizontal'
            disableDraggingSelection
            disableDraggingOverlay
            initialBrushPosition={initialBrushPosition}
            onChange={handleBrushChange}
            selectedBoxStyle={{
              stroke: twColors.gray[500],
              fill: "#044c9929",
            }}
            renderBrushHandle={BrushHandle}
            useWindowMoveEvents
          />
        </Group>
      </svg>

      {tooltipData ? (
        <TooltipContent
          tooltipData={tooltipData}
          tooltipLeft={tooltipLeft}
          tooltipTop={tooltipTop}
          scenarioName={scenarioName}
          scenarioForecast={filteredScenarioForecast}
          dateColumn={dateColumn}
          targetColumn={targetColumn}
          doesDateContainTime={doesDateContainTime}
        />
      ) : null}

      {isLoadingForecastData ? (
        <div className='flex justify-center items-center gap-2 inset-0 absolute bg-background/60'>
          <LoadingBackdrop message='Calculating...' />
        </div>
      ) : null}
    </div>
  );
};

const ChartLegend = ({ scenarioName }: { scenarioName?: string }) => {
  return (
    <div className='flex gap-2.5 h-[30px] text-gray-400'>
      <span className='flex gap-2 items-center'>
        <span className='w-[10px] border-t-[1.5px] border-gray-500' />
        <span>History</span>
      </span>
      <span className='flex gap-2 items-center'>
        <span className='w-[10px] border-t-[3px] border-[hsl(var(--primary))]' />
        <span>Original forecast</span>
      </span>
      {scenarioName ? (
        <span className='flex gap-2 items-center'>
          <span className='w-[10px] border-t-[3px] border-[#589FA3]' />
          <span>{scenarioName}</span>
        </span>
      ) : null}
    </div>
  );
};

const BrushHandle = ({ x, height, isBrushActive }: BrushHandleRenderProps) => {
  const pathWidth = 8;
  const pathHeight = 15;
  if (!isBrushActive) {
    return null;
  }
  return (
    <Group left={x + pathWidth / 2} top={(height - pathHeight) / 2}>
      <path
        fill='#f2f2f2'
        d='M -4.5 0.5 L 3.5 0.5 L 3.5 15.5 L -4.5 15.5 L -4.5 0.5 M -1.5 4 L -1.5 12 M 0.5 4 L 0.5 12'
        stroke='#999999'
        strokeWidth='1'
        style={{ cursor: "ew-resize" }}
      />
    </Group>
  );
};

const tooltipStyles: React.CSSProperties = {
  ...defaultStyles,
  display: "flex",
  flexDirection: "column",
  gap: "12px",
  width: "260px",
  backgroundColor: "hsl(var(--muted))",
  color: twColors.gray[400],
  border: "1px solid hsl(var(--border))",
  padding: "12px",
};

const TooltipContent = ({
  tooltipData,
  tooltipLeft,
  tooltipTop,
  scenarioName,
  scenarioForecast,
  dateColumn,
  targetColumn,
  doesDateContainTime = false,
}: {
  tooltipData: ScoringData | ForecastData;
  tooltipLeft: number;
  tooltipTop: number;
  scenarioName: string;
  scenarioForecast: ForecastData[];
  dateColumn: string;
  targetColumn: string;
  doesDateContainTime: boolean;
}) => {
  const isScoringData = targetColumn in tooltipData;

  const date = useMemo(() => {
    const dateToFormat = momentDate(
      isScoringData ? tooltipData[dateColumn] : tooltipData.timestamp
    );

    const day = dateToFormat.getDate().toString().padStart(2, "0");
    const month = (dateToFormat.getMonth() + 1).toString().padStart(2, "0");
    const year = dateToFormat.getFullYear();

    let formattedDate = `${day}/${month}/${year}`;

    if (doesDateContainTime) {
      const hours = dateToFormat.getHours().toString().padStart(2, "0");
      const minutes = dateToFormat.getMinutes().toString().padStart(2, "0");
      formattedDate = `${formattedDate} ${hours}:${minutes}`;
    }

    return formattedDate;
  }, [isScoringData, tooltipData]);

  const scenarioForecastValue = useMemo(() => {
    if (!scenarioForecast) return null;

    const forecastDataPoint = scenarioForecast.find(
      (d) => d.timestamp === (tooltipData as ForecastData).timestamp
    );

    return forecastDataPoint?.prediction;
  }, [scenarioForecast, tooltipData]);

  if (isScoringData) {
    return (
      <TooltipWithBounds
        top={tooltipTop}
        left={tooltipLeft}
        style={tooltipStyles}
      >
        <div className='font-semibold text-gray-200'>{date}</div>
        <div className='flex items-center justify-between'>
          <span className='flex gap-2 items-center'>
            <span className='w-[10px] border-t-[1.5px] border-[hsl(var(--primary))]' />
            <span>{targetColumn}</span>
          </span>
          <span>{tooltipData[targetColumn]}</span>
        </div>
      </TooltipWithBounds>
    );
  }

  return (
    <TooltipWithBounds
      top={tooltipTop}
      left={tooltipLeft}
      style={tooltipStyles}
    >
      <div className='font-semibold text-gray-200'>{date}</div>
      <div className='flex items-center justify-between w-full'>
        <span className='flex flex-1 gap-2 items-center overflow-hidden'>
          <span className='flex-shrink-0 w-[10px] border-t-[3px] border-[hsl(var(--primary))]' />
          <span>Original forecast</span>
        </span>
        <span>{tooltipData.prediction.toFixed(2)}</span>
      </div>
      <div className='flex items-center justify-between'>
        <span className='flex gap-2 items-center'>
          <span className='w-[10px] border-t-[3px] border-[#589FA3]' />
          <span className='truncate'>{scenarioName || "Scenario"}</span>
        </span>
        <span>{scenarioForecastValue?.toFixed(2)}</span>
      </div>
    </TooltipWithBounds>
  );
};

export default WhatIfScenariosLineChart;
