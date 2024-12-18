import { useMemo } from "react";
import { format as d3Format } from "d3";
import { scaleTime, scaleLinear } from "@visx/scale";
import { Group } from "@visx/group";
import { LinePath } from "@visx/shape";
import { AxisBottom, AxisLeft } from "@visx/axis";
import { GridRows } from "@visx/grid";
import useMeasure from "react-use-measure";
import { type FeatureRecord } from "~/helpers";
import { NumberValue } from "d3";
import twColors from "tailwindcss/colors";

type DataProp = "forecast" | "xempValue" | "featureValue";

type Props = {
  data: FeatureRecord[];
  dataType?: DataProp;
  showBottomAxis?: boolean;
};

const getXValue = (d: FeatureRecord) => (d?.date ? new Date(d.date) : null);

const getYValue = (d: FeatureRecord, dataType: DataProp) => {
  switch (dataType) {
    case "forecast":
      return d.prediction;
    case "xempValue":
      return d.strength;
    case "featureValue":
    default:
      return d.featureValue;
  }
};

const margin = {
  top: 5,
  right: 5,
  bottom: 25,
  left: 60,
};

const XEMPModalLineChart = ({
  data,
  dataType = "forecast",
  showBottomAxis = false,
}: Props) => {
  const [ref, bounds] = useMeasure();

  const { leftAxisLabel, lineColor, formatTick } = useMemo(() => {
    switch (dataType) {
      case "forecast":
        return {
          leftAxisLabel: "Forecast",
          lineColor: "hsl(var(--primary))",
          formatTick: (value: NumberValue) => d3Format(".2s")(value).toString(),
        };
      case "xempValue":
        return {
          leftAxisLabel: "XEMP value",
          lineColor: "white",
          formatTick: (value: NumberValue) => value.toString(),
        };
      case "featureValue":
      default:
        return {
          leftAxisLabel: "Feature value",
          lineColor: "#DA772D",
          formatTick: (value: NumberValue) => d3Format(".2s")(value).toString(),
        };
    }
  }, [dataType]);

  const sortedData = useMemo(() => {
    return data.sort((a, b) => {
      return a.date.localeCompare(b.date);
    });
  }, [data]);

  const { xMax, yMax } = useMemo(() => {
    const width = bounds.width || 100;
    const height = bounds.height || 100;

    const xMax = width - margin.left - margin.right;
    const yMax = height - margin.top - margin.bottom;

    return { xMax, yMax };
  }, [bounds]);

  const xScale = useMemo(() => {
    return scaleTime({
      domain: [
        new Date(sortedData[0].date),
        new Date(sortedData[sortedData.length - 1].date),
      ],
      range: [0, xMax],
    });
  }, [sortedData, bounds.width]);

  const yScale = useMemo(() => {
    const minYValue = Math.min(
      ...sortedData.map((d) => {
        return getYValue(d, dataType);
      })
    );
    const maxYValue = Math.max(
      ...sortedData.map((d) => getYValue(d, dataType))
    );
    const maxDomain = Math.max(Math.abs(minYValue), Math.abs(maxYValue));
    return scaleLinear({
      domain:
        dataType === "xempValue"
          ? [-maxDomain, maxDomain]
          : [minYValue, maxYValue],
      range: [yMax, 0],
    });
  }, [sortedData, bounds.height, dataType]);

  const xempAxisYScale = useMemo(
    () =>
      scaleLinear({
        domain: [-1, 1],
        range: [yMax, 0],
      }),
    [yMax]
  );

  return (
    <div className='h-[140px]'>
      <svg ref={ref} width='100%' height='100%'>
        <Group left={margin.left} top={margin.top}>
          <GridRows
            scale={yScale}
            width={xMax}
            height={yMax}
            numTicks={5}
            stroke={twColors.gray[700]}
          />
          <AxisLeft
            scale={dataType === "xempValue" ? xempAxisYScale : yScale}
            stroke={twColors.gray[500]}
            tickStroke={twColors.gray[500]}
            tickLabelProps={{ fill: twColors.gray[400] }}
            tickClassName='uppercased'
            numTicks={5}
            label={leftAxisLabel}
            labelProps={{ fill: twColors.gray[200] }}
            tickFormat={formatTick}
            tickValues={dataType === "xempValue" ? [-1, 0, 1] : undefined}
          />
          {showBottomAxis ? (
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
              labelProps={{ fill: twColors.gray[200] }}
              tickClassName='uppercased'
              numTicks={5}
              tickFormat={(date) => {
                if (date instanceof Date) {
                  const day = date.getDate().toString().padStart(2, "0");
                  const month = (date.getMonth() + 1)
                    .toString()
                    .padStart(2, "0");
                  const year = date.getFullYear();
                  return `${day}/${month}/${year}`;
                }
                return date.toString();
              }}
            />
          ) : null}
          <LinePath
            data={sortedData}
            x={(d) => xScale(getXValue(d) ?? new Date())}
            y={(d) => yScale(getYValue(d, dataType))}
            stroke={lineColor}
            strokeWidth={1.5}
          />
        </Group>
      </svg>
    </div>
  );
};

export default XEMPModalLineChart;
