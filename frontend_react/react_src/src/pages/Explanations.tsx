import { Fragment, useState, useMemo, useContext, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faXmark } from "@fortawesome/free-solid-svg-icons/faXmark";
import { faPlus } from "@fortawesome/free-solid-svg-icons/faPlus";
import { faArrowsRotate } from "@fortawesome/free-solid-svg-icons/faArrowsRotate";
import { faCalendarDays } from "@fortawesome/free-solid-svg-icons/faCalendarDays";
import { faMapPin } from "@fortawesome/free-solid-svg-icons/faMapPin";
import { faEye } from "@fortawesome/free-solid-svg-icons/faEye";
import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import twColors from "tailwindcss/colors";
import { Button } from "~/components/ui/button";
import { Tabs, TabsList, TabsTrigger } from "~/components/ui/tabs";
import { Switch } from "~/components/ui/switch";
import { Label } from "~/components/ui/label";
import { Alert, AlertDescription, AlertTitle } from "~/components/ui/alert";
import { Input } from "~/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import LoadingBackdrop from "~/components/ui-custom/LoadingBackdrop";
import ExplanationsLineChart from "~/components/ExplanationsLineChart";
import XEMPLineChart from "~/components/XEMPLineChart";
import XEMPFeaturesModal from "~/components/XEMPFeaturesModal";
import DateTimePicker from "~/components/ui-custom/DateTimePicker";
import { AppStateContext, type Feature } from "~/state/AppState";
import {
  formatXEMPFeatures,
  getDatePickerTimeConstraints,
  type FormattedXEMPFeature,
} from "~/helpers";
import drIcon from "~/assets/dr-chat-icon.png";

const Explanations = () => {
  const { scoringData, appSettings } = useContext(AppStateContext);
  const { target: targetColumn } = appSettings;
  return (
    <div className='flex flex-col gap-10 p-6'>
      <div>
        <h3 className='mb-1 text-2xl text-white'>Explanations</h3>
        <p className='text-gray-400'>
          {`Explore how different features affect the forecasted values of
          “${targetColumn}”.`}
        </p>
      </div>
      {scoringData.length === 0 ? (
        <Alert>
          <FontAwesomeIcon icon={faExclamationTriangle} />
          <AlertTitle>No data available</AlertTitle>
          <AlertDescription className='text-gray-400'>
            Filters combination does not return any data. Please adjust the
            filters.
          </AlertDescription>
        </Alert>
      ) : (
        <Fragment>
          <ForecastSection />
          <div className='grid grid-cols-2 gap-10 h-[800px]'>
            <XEMPExplanations />
            <Summary />
          </div>
        </Fragment>
      )}
    </div>
  );
};

const ForecastSection = () => {
  const {
    appSettings,
    forecastData,
    forecastDataLoading,
    selectedFeatures,
    confidenceIntervalEnabled,
    predictionExplanationsEnabled,
    toggleConfidenceInterval,
    togglePredictionExplanations,
    addPredictionFeature,
    removePredictionFeature,
    resetPredictionFeatures,
  } = useContext(AppStateContext);
  const { target: targetColumn } = appSettings;

  return (
    <div className='flex flex-col gap-4'>
      <div className='flex flex-col gap-1'>
        <h4 className='text-lg font-medium'>Forecast</h4>
        <p className='text-gray-400'>
          {`Visualize the forecast of “${targetColumn}” and optionally add layers of
          additional insight.`}
        </p>
        <div className='flex flex-col gap-4 p-4 rounded border'>
          <div className='flex flex-col gap-2'>
            <TogglerWithDescription
              id='confidence-interval'
              checked={confidenceIntervalEnabled}
              labelText='Confidence interval'
              subText='Show the confidence interval of the forecasted values.'
              onChange={toggleConfidenceInterval}
            />
            {confidenceIntervalEnabled ? (
              <div className='flex flex-col gap-4 items-start ml-[3.25rem]'>
                <div>
                  <Input value={80} disabled />
                </div>
                {forecastData.length === 0 && !forecastDataLoading ? (
                  <Alert>
                    <FontAwesomeIcon icon={faExclamationTriangle} />
                    <AlertTitle>No forecast data available</AlertTitle>
                    <AlertDescription className='text-gray-400'>
                      Please calculate the forecast first.
                    </AlertDescription>
                  </Alert>
                ) : null}
              </div>
            ) : null}
          </div>
          <div className='flex flex-col gap-2'>
            <TogglerWithDescription
              id='prediction-explanations'
              checked={predictionExplanationsEnabled}
              labelText='Prediction explanations'
              subText='Show the prediction explanations of the forecasted values.'
              onChange={togglePredictionExplanations}
            />
            {predictionExplanationsEnabled ? (
              <div className='flex items-center justify-between ml-[3.25rem]'>
                <div className='flex items-center gap-1'>
                  {selectedFeatures.map((feature) => (
                    <FeatureCard
                      key={feature.name}
                      feature={feature}
                      onRemove={() => {
                        removePredictionFeature(feature);
                      }}
                    />
                  ))}
                  <FeaturesDropdown
                    selectedFeatures={selectedFeatures}
                    onAdd={(feature: Feature) => addPredictionFeature(feature)}
                  />
                </div>
                <Button
                  size='sm'
                  variant='ghost'
                  onClick={resetPredictionFeatures}
                >
                  <FontAwesomeIcon icon={faArrowsRotate} className='mr-2' />
                  Reset selections
                </Button>
              </div>
            ) : null}
          </div>
        </div>
      </div>
      <ExplanationsLineChart />
    </div>
  );
};

const TogglerWithDescription = ({
  id,
  checked,
  labelText,
  subText,
  onChange,
}: {
  id: string;
  checked: boolean;
  labelText: string;
  subText: string;
  onChange: (checked: boolean) => void;
}) => {
  return (
    <div className='flex gap-2'>
      <Switch id={id} checked={checked} onCheckedChange={onChange} />
      <div className='flex flex-col gap-1'>
        <Label htmlFor={id}>{labelText}</Label>
        <div className='text-gray-400'>{subText}</div>
      </div>
    </div>
  );
};

const FeatureCard = ({
  feature,
  onRemove,
}: {
  feature: Feature;
  onRemove: () => void;
}) => {
  const { name, color } = feature;

  return (
    <div className='flex items-center gap-2 py-1 px-2 rounded max-w-[130px] bg-muted'>
      <div
        className='flex-shrink-0 w-3 h-3 rounded-sm'
        style={{
          backgroundColor: color,
        }}
      />
      <div className='text-xs truncate' title={name}>
        {name}
      </div>
      <FontAwesomeIcon
        icon={faXmark}
        className='cursor-pointer'
        onClick={onRemove}
      />
    </div>
  );
};

const FeaturesDropdown = ({
  selectedFeatures,
  onAdd,
}: {
  selectedFeatures: Feature[];
  onAdd: (feature: Feature) => void;
}) => {
  const { importantFeaturesWithColors } = useContext(AppStateContext);

  const filteredFeaturesOptions = useMemo(() => {
    // Keep only the unselected features
    const filtered = importantFeaturesWithColors.filter(
      (feature) => !selectedFeatures.find((f) => f.name === feature.name)
    );

    const formattedFilteredOptions = filtered.map(({ name }) => {
      return {
        key: name,
        title: name,
      };
    });

    return formattedFilteredOptions;
  }, [selectedFeatures]);

  const canAddFeature =
    selectedFeatures.length < 5 && filteredFeaturesOptions.length > 0;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          size='sm'
          variant='ghost'
          onClick={() => null}
          disabled={!canAddFeature}
        >
          <FontAwesomeIcon icon={faPlus} className='mr-2' />
          Add feature
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className='w-56'>
        {filteredFeaturesOptions.map((option) => (
          <DropdownMenuItem
            key={option.key}
            onSelect={() => {
              const selectedFeature = importantFeaturesWithColors.find(
                (feature) => feature.name === option.key
              );
              if (!selectedFeature) {
                return;
              }
              onAdd(selectedFeature);
            }}
          >
            {option.title}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

const XEMPExplanations = () => {
  const { forecastData, doesDateContainTime, appSettings } =
    useContext(AppStateContext);
  const {
    timestep_settings: { timeStep, timeUnit },
  } = appSettings;
  const [activeTab, setActiveTab] = useState("full-forecast");
  const [selectedDate, setSelectedDate] = useState(new Date());

  const { features: formattedFeatures, allDates } = useMemo(() => {
    return formatXEMPFeatures(forecastData);
  }, [forecastData]);

  const seriesCount = useMemo(
    () => new Set(forecastData.map(({ seriesId }) => seriesId)).size,
    [forecastData]
  );

  const isFullForecastMode = useMemo(
    () => activeTab === "full-forecast",
    [activeTab]
  );

  const enableControls = useMemo(
    () => formattedFeatures.length > 0,
    [formattedFeatures]
  );

  const datePickerTimeConstraints = useMemo(() => {
    if (doesDateContainTime) {
      return getDatePickerTimeConstraints(timeStep, timeUnit);
    }

    return undefined;
  }, [doesDateContainTime, timeStep, timeUnit]);

  useEffect(() => {
    if (allDates.length > 0) {
      setSelectedDate(new Date(allDates[0]));
    }
  }, [allDates]);

  return (
    <div className='flex flex-col gap-4 overflow-y-hidden'>
      <div>
        <h4 className='mb-1 text-lg font-medium'>XEMP Explanations</h4>
        <p className='text-gray-400'>
          See how individual features affected the forecast, based on XEMP
          values.
        </p>
      </div>
      <div className='flex flex-col gap-2'>
        <div>View explanations for:</div>
        <div className='flex justify-between gap-2'>
          <Tabs
            defaultValue='full-forecast'
            className='flex flex-col gap-4 items-start'
            onValueChange={(value) => setActiveTab(value)}
          >
            <TabsList>
              <TabsTrigger value='full-forecast'>
                <FontAwesomeIcon className='mr-2' icon={faCalendarDays} />
                Full forecast
              </TabsTrigger>
              <TabsTrigger value='single-date'>
                <FontAwesomeIcon className='mr-2' icon={faMapPin} />
                Single date
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <DateTimePicker
            value={selectedDate}
            inputProps={{
              disabled: isFullForecastMode || !enableControls,
            }}
            startDate={allDates[0]}
            endDate={allDates[allDates.length - 1] || new Date().toDateString()}
            timeFormat={doesDateContainTime ? "HH:mm" : false}
            timeConstraints={datePickerTimeConstraints}
            onChange={(date) => setSelectedDate(new Date(date as string))}
          />
        </div>
      </div>
      <div className='flex-1 overflow-y-auto'>
        {isFullForecastMode ? (
          <FullForecastTable features={formattedFeatures} />
        ) : (
          <SingleDateTable
            features={formattedFeatures}
            selectedDate={selectedDate}
            seriesCount={seriesCount}
          />
        )}
      </div>
    </div>
  );
};

const FullForecastTable = ({
  features,
}: {
  features: FormattedXEMPFeature[];
}) => {
  const [selectedFeature, setSelectedFeature] = useState<string | null>(null);

  const tableRows = useMemo(() => {
    return features
      .map(({ feature, featureRecords, originalRecordsCount }) => {
        const totalStrength = featureRecords.reduce(
          (acc, { strength }) => acc + strength,
          0
        );
        const avgStrength = totalStrength / (originalRecordsCount || 1);

        return {
          feature,
          featureRecords,
          avgStrength,
        };
      })
      .sort((a, b) => {
        const aStrength = a.avgStrength;
        const bStrength = b.avgStrength;

        return Math.abs(bStrength) - Math.abs(aStrength);
      })
      .map(({ feature, featureRecords, avgStrength }) => {
        const isPositive = avgStrength > 0;
        const textColor = !isPositive ? twColors.blue[400] : twColors.red[400];

        return (
          <TableRow key={feature}>
            <TableCell>
              <div className='flex items-center gap-2 pr-2'>
                <div className='flex flex-shrink-0 gap-1 w-[100px]'>
                  <span style={{ color: `${textColor}` }}>
                    {isPositive ? "+" : "-"}
                  </span>
                  <span>{Math.abs(avgStrength).toFixed(2)}</span>
                </div>
                <XEMPLineChart data={featureRecords} />
              </div>
            </TableCell>
            <TableCell>
              <div className='flex items-center justify-between gap-2'>
                <span className='truncate' title={feature}>
                  {feature}
                </span>
                <Button
                  size='sm'
                  variant='ghost'
                  onClick={() => setSelectedFeature(feature)}
                >
                  <FontAwesomeIcon icon={faEye} />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        );
      });
  }, [features]);

  const isTableEmpty = useMemo(() => tableRows.length === 0, [tableRows]);

  if (isTableEmpty) {
    return (
      <div className='flex flex-col items-center justify-center h-[150px]'>
        <div>No data available</div>
      </div>
    );
  }

  return (
    <Fragment>
      <Table className='table-fixed'>
        <TableHeader>
          <TableRow>
            <TableHead className='w-[280px]'>
              Avg. XEMP value and trend
            </TableHead>
            <TableHead>Feature</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>{tableRows}</TableBody>
      </Table>
      {selectedFeature !== null && (
        <XEMPFeaturesModal
          allFeatures={features}
          selectedFeature={selectedFeature}
          setSelectedFeature={setSelectedFeature}
        />
      )}
    </Fragment>
  );
};

const SingleDateTable = ({
  features,
  selectedDate,
  seriesCount,
}: {
  features: FormattedXEMPFeature[];
  selectedDate: Date;
  seriesCount: number;
}) => {
  const tableRows = useMemo(() => {
    return features
      .map(({ feature, featureRecords }) => {
        let totalStrength = 0;
        let totalFeatureValues = 0;

        featureRecords.forEach(({ date, strength, featureValue }) => {
          if (new Date(date).toString() === selectedDate.toString()) {
            totalStrength += strength;
            totalFeatureValues += Number(featureValue);
          }
        });

        const avgStrength = totalStrength / (seriesCount || 1);
        const avgFeatureValue = totalFeatureValues / (seriesCount || 1);

        return {
          xempValue: { avgStrength },
          featureAndStrength: {
            feature,
            featureValue: avgFeatureValue,
          },
        };
      })
      .filter(({ xempValue }) => xempValue.avgStrength !== 0)
      .sort((a, b) => {
        const aStrength = a.xempValue.avgStrength;
        const bStrength = b.xempValue.avgStrength;

        return Math.abs(bStrength) - Math.abs(aStrength);
      })
      .map(({ xempValue, featureAndStrength }) => {
        const isPositive = xempValue.avgStrength > 0;
        const textColor = !isPositive ? twColors.blue[400] : twColors.red[400];

        const featureValue =
          typeof featureAndStrength.featureValue === "number" &&
          !isNaN(featureAndStrength.featureValue)
            ? Math.abs(featureAndStrength.featureValue).toFixed(2)
            : "-";

        return (
          <TableRow key={featureAndStrength.feature}>
            <TableCell>
              <div className='flex items-center gap-2 pr-2'>
                <div className='flex gap-1 w-[110px]'>
                  <span style={{ color: `${textColor}` }}>
                    {isPositive ? "+" : "-"}
                  </span>
                  <span>{Math.abs(xempValue.avgStrength).toFixed(2)}</span>
                </div>
              </div>
            </TableCell>
            <TableCell>
              <div className='flex flex-col gap-1 w-full'>
                <span className='truncate' title={featureAndStrength.feature}>
                  {featureAndStrength.feature}
                </span>
                <span className='text-gray-400'>{featureValue}</span>
              </div>
            </TableCell>
          </TableRow>
        );
      });
  }, [features, selectedDate]);

  const isTableEmpty = useMemo(() => tableRows.length === 0, [tableRows]);

  if (isTableEmpty) {
    return (
      <div className='flex flex-col items-center justify-center h-[150px]'>
        <div>No data available</div>
      </div>
    );
  }

  return (
    <Table className='table-fixed'>
      <TableHeader>
        <TableRow>
          <TableHead className='w-[200px]'>XEMP value</TableHead>
          <TableHead>Feature and avg. value</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>{tableRows}</TableBody>
    </Table>
  );
};

const Summary = () => {
  const { naturalLanguageSummary, naturalLanguageSummaryLoading } =
    useContext(AppStateContext);

  return (
    <div className='flex flex-col gap-4'>
      <div>
        <h4 className='mb-1 text-lg font-medium'>Natural Language Summary</h4>
        <p className='text-gray-400'>
          Understand the forecast in plain language.
        </p>
      </div>
      <div className='flex flex-col flex-1 gap-1'>
        <div className='flex flex-col flex-1 gap-3 p-3 relative overflow-y-auto rounded bg-muted/60'>
          {naturalLanguageSummaryLoading ? (
            <div className='flex items-center justify-center absolute inset-0'>
              <LoadingBackdrop message='Getting summary...' />
            </div>
          ) : null}
          {!naturalLanguageSummary && !naturalLanguageSummaryLoading ? (
            <div className='flex flex-col flex-1 gap-1 items-center justify-center'>
              <div>No summary available</div>
            </div>
          ) : null}
          {naturalLanguageSummary && !naturalLanguageSummaryLoading ? (
            <div className='flex gap-3 p-3 rounded border'>
              <img
                src={drIcon}
                className='flex-shrink-0 w-8 h-8'
                alt='DataRobot'
              />
              <span className='mt-2 whitespace-pre-wrap'>
                {naturalLanguageSummary}
              </span>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default Explanations;
