import { useMemo } from "react";
import { scaleTime, scaleLinear } from "@visx/scale";
import { Group } from "@visx/group";
import { LinePath, Line } from "@visx/shape";
import { AxisLeft } from "@visx/axis";
import useMeasure from "react-use-measure";
import twColors from "tailwindcss/colors";
import { momentDate, type FeatureRecord } from "~/helpers";

type Props = {
  data: FeatureRecord[];
};

const getXValue = (d: FeatureRecord) => (d?.date ? momentDate(d.date) : null);

const getYValue = (d: FeatureRecord) => d.strength;

const margin = {
  top: 5,
  right: 5,
  bottom: 5,
  left: 5,
};

const XEMPLineChart = ({ data }: Props) => {
  const [ref, bounds] = useMeasure();

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
        momentDate(sortedData[0].date),
        momentDate(sortedData[sortedData.length - 1].date),
      ],
      range: [0, xMax],
    });
  }, [sortedData, bounds.width]);

  const yScale = useMemo(() => {
    const minStrength = Math.min(...sortedData.map((d) => d.strength));
    const maxStrength = Math.max(...sortedData.map((d) => d.strength));
    const maxDomain = Math.max(Math.abs(minStrength), Math.abs(maxStrength));
    return scaleLinear({
      domain: [-maxDomain, maxDomain],
      range: [yMax, 0],
    });
  }, [sortedData, bounds.height]);

  const axisYScale = useMemo(
    () =>
      scaleLinear({
        domain: [-1, 1],
        range: [yMax, 0],
      }),
    [yMax]
  );

  return (
    <div className='h-[50px]'>
      <svg ref={ref} width='100%' height='100%'>
        <Group left={margin.left} top={margin.top}>
          <AxisLeft
            scale={axisYScale}
            stroke={twColors.gray[700]}
            tickStroke={twColors.gray[700]}
            tickValues={[-1, 0, 1]}
          />
          <Line
            from={{ x: 0, y: yMax / 2 }}
            to={{ x: xMax, y: yMax / 2 }}
            stroke={twColors.gray[700]}
            strokeWidth={1}
          />
          <LinePath
            data={sortedData}
            x={(d) => xScale(getXValue(d) ?? new Date())}
            y={(d) => yScale(getYValue(d))}
            stroke='hsl(var(--primary))'
            strokeWidth={1.5}
          />
        </Group>
      </svg>
    </div>
  );
};

export default XEMPLineChart;
