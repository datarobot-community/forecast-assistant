import moment from "moment";
import {
  ForecastData,
  Feature,
  ScoringData,
  WhatIfScenarioFeature,
} from "./state/AppState";
import { ImportantFeature, TimeUnit } from "./data/useConfigs";

type Explanation = { timestamp: string; feature: string; strength: number };

export type FeatureRecord = {
  date: string;
  strength: number;
  featureValue: number;
  prediction: number;
};

export type FormattedXEMPFeature = {
  feature: string;
  featureRecords: FeatureRecord[];
  originalRecordsCount?: number;
};

type TimeConstraint = {
  min: number;
  max: number;
  step: number;
};

type TimeConstraints = {
  hours?: TimeConstraint;
  minutes?: TimeConstraint;
};

export const formatStackedBarData = (
  data: ForecastData[],
  selectedFeatures: Feature[]
): { [key: string]: number | string }[] => {
  // Extract the prediction explanations and add the timestamp
  const predictionExplanations = data
    .map((row) => {
      const peRow = row.predictionExplanations.map((explanation) => {
        return {
          feature: explanation.feature,
          strength: explanation.strength,
          timestamp: row.timestamp,
        };
      });
      return peRow;
    })
    .flat();

  // Groupby timestamp and feature and sum the strength
  const groupedExplanations = predictionExplanations.reduce(
    (groupedData, current) => {
      const key = `${current.timestamp}-${current.feature}`;
      if (!groupedData[key]) {
        groupedData[key] = {
          timestamp: current.timestamp,
          feature: current.feature,
          strength: 0,
        };
      }
      groupedData[key].strength += current.strength;
      return groupedData;
    },
    {} as Record<string, Explanation>
  );

  // Convert the grouped object to an array
  const groupedExplanationsArray = Object.values(groupedExplanations);

  // Format the prediction explanations
  const formattedExplanations = groupedExplanationsArray.map((explanation) => {
    return {
      ...explanation,
      feature: selectedFeatures.some(
        (feature) => feature.name === explanation.feature
      )
        ? explanation.feature
        : "Other",
    };
  });

  // Groupby the formatted explanations by timestamp and feature and sum the strength
  const groupedFormattedExplanations = formattedExplanations.reduce(
    (groupedData, current) => {
      const key = `${current.timestamp}-${current.feature}`;
      if (!groupedData[key]) {
        groupedData[key] = {
          timestamp: current.timestamp,
          feature: current.feature,
          strength: 0,
        };
      }
      groupedData[key].strength += current.strength;
      return groupedData;
    },
    {} as Record<string, Explanation>
  );

  // Convert the grouped object to an array
  const groupedFormattedExplanationsArray = Object.values(
    groupedFormattedExplanations
  );

  const formattedData = groupedFormattedExplanationsArray.reduce(
    (groupedData, current) => {
      const key = current.timestamp;
      if (!groupedData[key]) {
        groupedData[key] = {
          date: current.timestamp as string,
        };
      }
      groupedData[key][current.feature] = current.strength;
      return groupedData;
    },
    {} as Record<string, { [key: string]: number | string }>
  );

  return Object.values(formattedData);
};

export const formatXEMPFeatures = (
  data: ForecastData[]
): {
  features: FormattedXEMPFeature[];
  allDates: string[];
} => {
  const features: {
    [key: string]: FormattedXEMPFeature;
  } = {};
  const groupedPredictions = data.reduce(
    (acc, d) => {
      const key = d.timestamp;
      if (!acc[key]) {
        acc[key] = 0;
      }
      acc[key] += d.prediction;
      return acc;
    },
    {} as Record<string, number>
  );

  data.forEach((item) => {
    item.predictionExplanations.forEach((explanation) => {
      const featureName = explanation.feature;
      if (!features[featureName]) {
        features[featureName] = {
          feature: featureName,
          featureRecords: [],
        };
      }
      // Check if the record already exists
      const existingRecord = features[featureName].featureRecords.find(
        (record) => record.date === item.timestamp
      );

      if (existingRecord) {
        existingRecord.strength += explanation.strength;
        existingRecord.featureValue += Number(explanation.featureValue);
        return;
      }

      features[featureName].featureRecords.push({
        date: item.timestamp,
        strength: explanation.strength,
        featureValue: Number(explanation.featureValue),
        prediction: groupedPredictions[item.timestamp],
      });
    });
  });

  // Fill in missing dates with strength of 0
  const allDates = [...new Set(data.map((item) => item.timestamp))].sort(
    (a, b) => a.localeCompare(b)
  );

  Object.values(features).forEach((feature) => {
    const datesWithStrengths = feature.featureRecords.map(
      (record) => record.date
    );
    const missingDates = allDates.filter(
      (date) => !datesWithStrengths.includes(date)
    );
    missingDates.forEach((date) => {
      feature.featureRecords.push({
        date,
        strength: 0,
        featureValue: 0,
        prediction: groupedPredictions[date] || 0,
      });
    });
    feature.featureRecords.sort((a, b) => a.date.localeCompare(b.date));
    // Store the original number of records to calculate the average strength
    feature.originalRecordsCount =
      feature.featureRecords.length - missingDates.length;
  });

  return { features: Object.values(features), allDates };
};

export const formatWhatIfScenarioData = (
  originalData: ScoringData[],
  scenarioFeatures: WhatIfScenarioFeature[],
  dateColumn: string,
  doesDateContainTime: boolean
): ScoringData[] => {
  // Overwrite the original data with the scenario features
  const updatedData = originalData.map((row) => {
    const updatedRow = { ...row };
    scenarioFeatures.forEach((feature) => {
      const scenarioValue = feature.values.find((value) => {
        // Reset seconds only if the date contains time
        if (doesDateContainTime) {
          return (
            momentDate(value.date).setSeconds(0).toString() ===
            momentDate(row[dateColumn]).setSeconds(0).toString()
          );
        }

        // Reset hours, minutes, and seconds if the date does not contain time
        return (
          momentDate(value.date).setHours(0, 0, 0, 0).toString() ===
          momentDate(row[dateColumn]).setHours(0, 0, 0, 0).toString()
        );
      });

      if (scenarioValue) {
        updatedRow[feature.featureName] = scenarioValue.value;
      }
    });
    return updatedRow;
  });

  return updatedData;
};

export const formatDateString = (
  dateString: string,
  format = "YYYY/MM/DD"
): string => {
  const date = moment.utc(dateString);
  return date.format(format);
};

export const momentDate = (date: string | number | Date) => {
  return moment(date).toDate();
};

const pythonToJavaScriptDateFormats: { [key: string]: string } = Object.freeze({
  "%A": "dddd",
  "%a": "ddd",
  "%B": "MMMM",
  "%b": "MMM",
  "%c": "ddd MMM DD HH:mm:ss YYYY",
  "%d": "DD",
  "%f": "SSS",
  "%H": "HH",
  "%I": "hh",
  "%j": "DDDD",
  "%M": "mm",
  "%m": "MM",
  "%p": "A",
  "%S": "ss",
  "%U": "ww",
  "%W": "ww",
  "%w": "d",
  "%X": "HH:mm:ss",
  "%x": "MM/DD/YYYY",
  "%Y": "YYYY",
  "%y": "YY",
  "%Z": "z",
  "%z": "ZZ",
  "%%": "%",
});

export const convertPythonDateFormatToJavaScript = (formatStr: string) => {
  for (const key in pythonToJavaScriptDateFormats) {
    formatStr = formatStr.split(key).join(pythonToJavaScriptDateFormats[key]);
  }
  return formatStr;
};

export const assignColorsToFeatures = (
  features: ImportantFeature[]
): Feature[] => {
  const featuresWithColors = features.map((feature) => {
    const color = `hsl(${Math.random() * 360}, 70%, 50%)`;
    return { name: feature.featureName, color };
  });

  return featuresWithColors;
};

export const getDatePickerTimeConstraints = (
  timeStep: number,
  timeUnit: TimeUnit
): TimeConstraints => {
  const timeConstraints: TimeConstraints = {
    hours: {
      min: 0,
      max: 23,
      step: 1,
    },
    minutes: {
      min: 0,
      max: 59,
      step: 1,
    },
  };

  switch (timeUnit) {
    case TimeUnit.HOUR:
      timeConstraints.hours = {
        min: 0,
        max: 23,
        step: timeStep,
      };
      timeConstraints.minutes = {
        min: 0,
        max: 0,
        step: 0,
      };
      break;
    case TimeUnit.MINUTE:
      timeConstraints.minutes = {
        min: 0,
        max: 59,
        step: timeStep,
      };
      break;
    default:
      break;
  }

  return timeConstraints;
};

export const getWhatIfScenarioMinMaxDate = (
  lastDate: Date,
  startValue: number,
  endValue: number,
  timeUnit: TimeUnit
) => {
  const minDate = momentDate(lastDate);
  const maxDate = momentDate(lastDate);

  const adjustDate = (date: Date, unit: TimeUnit, value: number) => {
    switch (unit) {
      case TimeUnit.YEAR:
        date.setFullYear(date.getFullYear() + value);
        break;
      case TimeUnit.QUARTER:
        date.setMonth(date.getMonth() + value * 3);
        break;
      case TimeUnit.MONTH:
        date.setMonth(date.getMonth() + value);
        break;
      case TimeUnit.WEEK:
        date.setDate(date.getDate() + value * 7);
        break;
      case TimeUnit.DAY:
        date.setDate(date.getDate() + value);
        break;
      case TimeUnit.HOUR:
        date.setHours(date.getHours() + value);
        break;
      case TimeUnit.MINUTE:
        date.setMinutes(date.getMinutes() + value);
        break;
      default:
        throw new Error(`Unsupported time unit: ${unit}`);
    }
  };

  adjustDate(minDate, timeUnit, startValue);
  adjustDate(maxDate, timeUnit, endValue);

  return { minDate: momentDate(minDate), maxDate: momentDate(maxDate) };
};

export const saveObjectToJSONFile = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  object: { [key: string]: any },
  filename: string
) => {
  const blob = new Blob([JSON.stringify(object, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename}.json`;
  a.click();
  URL.revokeObjectURL(url);
};

export const saveArrayToCSVFile = (
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  array: { [key: string]: any }[],
  filename: string
) => {
  const header = Object.keys(array[0]);
  const body = array.map((row) => {
    return header.map((fieldName) => {
      if (typeof row[fieldName] === "object") {
        return null;
      }
      return row[fieldName].toString();
    });
  });
  const csv = [header, ...body].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${filename}.csv`;
  a.click();
  URL.revokeObjectURL(url);
};
