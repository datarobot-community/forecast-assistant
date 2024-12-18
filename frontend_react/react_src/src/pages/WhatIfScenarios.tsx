import {
  Fragment,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { Navigate } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPlus } from "@fortawesome/free-solid-svg-icons/faPlus";
import { faChartLine } from "@fortawesome/free-solid-svg-icons/faChartLine";
import { faCode } from "@fortawesome/free-solid-svg-icons/faCode";
import { faTrashCan } from "@fortawesome/free-solid-svg-icons/faTrashCan";
import { faCopy } from "@fortawesome/free-solid-svg-icons/faCopy";
import { faFileCsv } from "@fortawesome/free-solid-svg-icons/faFileCsv";
import { faFileLines } from "@fortawesome/free-solid-svg-icons/faFileLines";
import { faRotateLeft } from "@fortawesome/free-solid-svg-icons/faRotateLeft";
import { faCheck } from "@fortawesome/free-solid-svg-icons/faCheck";
import { faPlay } from "@fortawesome/free-solid-svg-icons/faPlay";
import { faCircleNotch } from "@fortawesome/free-solid-svg-icons/faCircleNotch";
import { faExclamationTriangle } from "@fortawesome/free-solid-svg-icons";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "~/components/ui/accordion";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import { Badge } from "~/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "~/components/ui/alert";
import DateTimePicker from "~/components/ui-custom/DateTimePicker";
import InfoTooltip from "~/components/ui-custom/InfoTooltip";
import WhatIfScenariosLineChart from "~/components/WhatIfScenariosLineChart";
import BulkScenarioEditorModal, {
  type Customizations,
} from "~/components/BulkScenarioEditorModal";
import { cn } from "~/lib/utils";
import calculatePredictions from "~/api/calculatePredictions";
import {
  formatWhatIfScenarioData,
  getDatePickerTimeConstraints,
  getWhatIfScenarioMinMaxDate,
  momentDate,
  saveObjectToJSONFile,
  saveArrayToCSVFile,
} from "~/helpers";
import {
  AppStateContext,
  WhatIfScenarioFeature,
  type WhatIfScenario,
} from "~/state/AppState";
import { ROUTES } from "~/pages/routes";

const WhatIfScenarios = () => {
  const { filters, forecastData, forecastSeriesIdsCount, appSettings } =
    useContext(AppStateContext);
  const {
    multiseries_id_column: multiseriesIdColumn,
    what_if_features: whatIfFeatures,
  } = appSettings;

  const isPageEnabled = useMemo(() => {
    const firstMultiseriesId = multiseriesIdColumn?.[0] || "";
    // If there is no forecast data, the page should be disabled
    if (forecastData.length < 1) {
      return false;
    }

    // If there is no filter, the page should be disabled
    if (
      filters?.[firstMultiseriesId] &&
      filters[firstMultiseriesId]?.length === 1
    ) {
      return true;
    }

    // If there is only one forecast series, the page should be enabled
    if (forecastSeriesIdsCount === 1) {
      return true;
    }

    return false;
  }, [filters, multiseriesIdColumn, forecastSeriesIdsCount]);

  const isWhatIfScenariosAvailable = useMemo(() => {
    if (!whatIfFeatures) return false;

    return whatIfFeatures.some((feature) => feature.known_in_advance);
  }, [whatIfFeatures]);

  // Redirect to the explanations page if the What-If scenarios is not available
  if (!isWhatIfScenariosAvailable) {
    return <Navigate to={ROUTES.EXPLANATIONS} />;
  }

  return (
    <div className='flex flex-col gap-10 p-6'>
      <h3 className='mb-1 text-2xl text-white'>What-If Scenarios</h3>
      <Forecasts />
      {!isPageEnabled ? (
        <Alert>
          <FontAwesomeIcon icon={faExclamationTriangle} />
          <AlertTitle>No data available</AlertTitle>
          <AlertDescription className='text-gray-400'>
            To view What-If scenarios, please select a single series from the
            filters and ensure that the forecast data is calculated.
          </AlertDescription>
        </Alert>
      ) : (
        <Fragment>
          <WhatIfScenariosLineChart />
          <Scenarios />
        </Fragment>
      )}
    </div>
  );
};

const Forecasts = () => {
  return (
    <div className='flex flex-col gap-1'>
      <h4 className='text-lg font-medium'>Forecasts</h4>
      <p className='text-gray-400'>
        Visually compare the forecasts of different scenarios, configured below.
      </p>
    </div>
  );
};

const Scenarios = () => {
  return (
    <div className='flex flex-col gap-4'>
      <h4 className='text-lg font-medium'>Scenarios</h4>
      <div className='flex h-[700px] overflow-hidden rounded border'>
        <ScenariosSidebar />
        <ScenarioDetails />
      </div>
    </div>
  );
};

const ScenariosSidebar = () => {
  const {
    forecastData,
    whatIfScenarios,
    activeWhatIfScenarioId,
    addWhatIfScenario,
    setActiveWhatIfScenarioId,
  } = useContext(AppStateContext);

  const originalForecastPredictionAvg = useMemo(() => {
    if (!forecastData) {
      return 0;
    }

    const predictions = forecastData.map((d) => d.prediction);
    return (
      predictions.reduce((acc, curr) => acc + curr, 0) / predictions.length
    );
  }, [forecastData]);

  const handleAddScenario = () => {
    addWhatIfScenario();
  };

  return (
    <div className='flex flex-col gap-2 w-[300px] border-r bg-muted/30'>
      <div className='flex-1 overflow-y-auto'>
        {whatIfScenarios.map((scenario) => (
          <ScenariosSidebarItem
            key={scenario.id}
            scenario={scenario}
            originalForecastPredictionAvg={originalForecastPredictionAvg}
            isActive={activeWhatIfScenarioId === scenario.id}
            onSelect={() => setActiveWhatIfScenarioId(scenario.id)}
          />
        ))}
      </div>
      <div className='p-1 border-t'>
        <Button variant='ghost' onClick={handleAddScenario}>
          <FontAwesomeIcon icon={faPlus} className='mr-2' />
          Add scenario
        </Button>
      </div>
    </div>
  );
};

const ScenariosSidebarItem = ({
  scenario,
  originalForecastPredictionAvg,
  isActive,
  onSelect,
}: {
  scenario: WhatIfScenario;
  originalForecastPredictionAvg: number;
  isActive: boolean;
  onSelect: () => void;
}) => {
  const { name, description, isLoadingForecastData } = scenario;

  const {
    averagePredictionDifference,
    textColor: avgDifferenceTextColor,
    isPositive: isAvgDifferencePositive,
  } = useMemo(() => {
    if (!scenario.forecastData) {
      return {
        averagePredictionDifference: 0,
        textColor: "",
        isPositive: false,
      };
    }

    const predictions = scenario.forecastData.map((d) => d.prediction);
    const secenarioPredictionsAvg =
      predictions.reduce((acc, curr) => acc + curr, 0) / predictions.length;
    const isPositive = secenarioPredictionsAvg >= originalForecastPredictionAvg;

    return {
      averagePredictionDifference:
        (secenarioPredictionsAvg * 100) / originalForecastPredictionAvg - 100,
      textColor: isPositive ? "text-green-500" : "text-red-500",
      isPositive,
    };
  }, [scenario.forecastData, originalForecastPredictionAvg]);

  return (
    <div
      className={cn(
        "flex flex-col gap-2 p-4 cursor-pointer border-l-4 border-l-transparent border-b",
        {
          "border-l-blue-400 bg-muted/50": isActive,
          "hover:bg-muted/60": !isActive,
        }
      )}
      onClick={onSelect}
    >
      <div className='flex flex-col gap-1'>
        <div className='flex justify-between items-center'>
          <div className='flex items-center gap-1'>
            <div className='w-2.5 h-2.5 rounded-full bg-blue-400' />
            <span className='body'>{name}</span>
          </div>
          {isLoadingForecastData ? (
            <FontAwesomeIcon
              icon={faCircleNotch}
              className='text-blue-400'
              spin
            />
          ) : null}
        </div>
        <p className='text-gray-400'>{description}</p>
      </div>
      <div className='flex items-center gap-2'>
        <FontAwesomeIcon icon={faChartLine} className='text-gray-400' />
        {avgDifferenceTextColor === "" ? (
          <span className='text-gray-500'>N/A</span>
        ) : (
          <div className='flex items-center gap-1'>
            <span className={avgDifferenceTextColor}>
              {`${isAvgDifferencePositive ? "+" : "-"}${Math.abs(Number(averagePredictionDifference.toFixed(2)))}%`}
            </span>
            <InfoTooltip text='Average % change in scenario from baseline' />
          </div>
        )}
      </div>
    </div>
  );
};

const ScenarioDetails = () => {
  const {
    appSettings,
    scoringData,
    inputDateFormat,
    outputDateFormat,
    doesDateContainTime,
    whatIfScenarios,
    activeWhatIfScenarioId: activeId,
    removeWhatIfScenario,
    duplicateWhatIfScenario,
    updateWhatIfScenario,
    setWhatIfScenarioForecastData,
    setWhatIfScenarioLoadingForecastData,
  } = useContext(AppStateContext);
  const { datetime_partition_column: dateColumn } = appSettings;
  const [doesScenarioNeedUpdate, setDoesScenarioNeedUpdate] = useState(false);

  const scenario = useMemo(
    () => whatIfScenarios.find((s) => s.id === activeId),
    [whatIfScenarios, activeId]
  );

  const [currentScenario, setCurrentScenario] = useState<
    WhatIfScenario | undefined
  >(scenario);
  const { name, description } = currentScenario || {};

  const onNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newName = e.currentTarget.value;
    setCurrentScenario((prev) => {
      if (!prev) return prev;
      return { ...prev, name: newName };
    });
    setDoesScenarioNeedUpdate(true);
  };

  const onDescriptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newDescription = e.currentTarget.value;
    setCurrentScenario((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        description: newDescription,
      };
    });
    setDoesScenarioNeedUpdate(true);
  };

  const onRunPrediction = async () => {
    if (currentScenario) {
      // Do nothing if the scenario is not ready
      if (
        currentScenario.features.length < 1 ||
        currentScenario.features.every((f) => f.values.length < 1)
      ) {
        return;
      }

      updateWhatIfScenario(currentScenario);
      try {
        setWhatIfScenarioLoadingForecastData(currentScenario.id, true);
        const { data } = await calculatePredictions({
          scoringData: formatWhatIfScenarioData(
            scoringData,
            currentScenario.features,
            dateColumn,
            doesDateContainTime
          ),
          dateColumn,
          inputDateFormat,
          outputDateFormat,
        });
        setWhatIfScenarioForecastData(currentScenario.id, data);
        setDoesScenarioNeedUpdate(false);
      } catch (error) {
        setWhatIfScenarioForecastData(currentScenario.id, []);
      }
    }
  };

  const onRemoveScenario = () => {
    if (currentScenario) {
      removeWhatIfScenario(currentScenario.id);
      setCurrentScenario(undefined);
    }
  };

  const onDuplicateScenario = () => {
    if (currentScenario) {
      duplicateWhatIfScenario(currentScenario.id);
    }
  };

  const onExportScenario = (type: string) => {
    if (!currentScenario || !currentScenario?.forecastData?.length) {
      return;
    }

    if (type === "export-json") {
      saveObjectToJSONFile(
        {
          forecast: currentScenario.forecastData,
          features: currentScenario.features,
        },
        currentScenario.name
      );
    } else {
      saveArrayToCSVFile(currentScenario.forecastData, currentScenario.name);
    }
  };

  useEffect(() => {
    setCurrentScenario(scenario);
    setDoesScenarioNeedUpdate(false);
  }, [scenario]);

  if (!currentScenario) {
    return (
      <div className='flex flex-col flex-1 gap-1 items-center justify-center text-center'>
        <div>No scenario is selected</div>
        <p className='text-gray-400'>
          Select a scenario from the sidebar to view the details.
        </p>
      </div>
    );
  }

  return (
    <div className='flex flex-col flex-1 gap-6 p-4 overflow-y-auto'>
      <div className='flex items-center justify-between'>
        <h5 className='font-medium text-base'>Scenario details</h5>
        <div className='flex gap-1'>
          <Button
            variant='ghost'
            disabled={currentScenario.isLoadingForecastData}
            onClick={onRunPrediction}
          >
            <FontAwesomeIcon icon={faPlay} className='mr-2' />
            Run prediction
          </Button>
          <Button variant='ghost' onClick={onDuplicateScenario}>
            <FontAwesomeIcon icon={faCopy} className='mr-2' />
            Duplicate
          </Button>
          <Button variant='ghost' onClick={onRemoveScenario}>
            <FontAwesomeIcon icon={faTrashCan} className='mr-2' />
            Delete
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant='outline'>Export</Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className='w-44'>
              <DropdownMenuItem
                disabled={!currentScenario.forecastData?.length}
                onSelect={() => onExportScenario("export-json")}
              >
                <FontAwesomeIcon icon={faCode} className='mr-2' />
                <span>Export as JSON</span>
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={!currentScenario.forecastData?.length}
                onSelect={() => onExportScenario("export-csv")}
              >
                <FontAwesomeIcon icon={faFileCsv} className='mr-2' />
                <span>Export as CSV</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <div className='flex flex-col gap-4 max-w-[500px]'>
        <div className='flex flex-col gap-1.5 w-full'>
          <Label htmlFor='name'>Name</Label>
          <Input
            id='name'
            placeholder='Name...'
            value={name}
            onChange={onNameChange}
          />
        </div>
        <div className='flex flex-col gap-1.5 w-full'>
          <Label htmlFor='description'>Description</Label>
          <Input
            id='description'
            placeholder='Description...'
            value={description}
            onChange={onDescriptionChange}
          />
        </div>
      </div>
      <ScenarioCustomizations
        originalScenario={scenario}
        scenario={currentScenario}
        doesScenarioNeedUpdate={doesScenarioNeedUpdate}
        setCurrentScenario={(scenario) => setCurrentScenario(scenario)}
        setDoesScenarioNeedUpdate={setDoesScenarioNeedUpdate}
      />
    </div>
  );
};

const ScenarioCustomizations = ({
  originalScenario,
  scenario,
  doesScenarioNeedUpdate,
  setCurrentScenario,
  setDoesScenarioNeedUpdate,
}: {
  originalScenario?: WhatIfScenario;
  scenario: WhatIfScenario;
  doesScenarioNeedUpdate: boolean;
  setCurrentScenario: (scenario: WhatIfScenario) => void;
  setDoesScenarioNeedUpdate: (value: boolean) => void;
}) => {
  const { appSettings, scoringData, updateWhatIfScenario } =
    useContext(AppStateContext);
  const {
    target: targetColumn,
    datetime_partition_column: dateColumn,
    what_if_features: whatIfFeatures,
    forecast_window_start: forecastWindowStart,
    forecast_window_end: forecastWindowEnd,
    timestep_settings: { timeUnit },
  } = appSettings;
  const [showBulkScenarioEditorModal, setShowBulkScenarioEditorModal] =
    useState(false);

  const features = useMemo(() => scenario.features, [scenario]);

  const { minDate, maxDate } = useMemo(() => {
    // Filter out the null target values
    const filtered = scoringData.filter((d) => d[targetColumn] !== null);
    const dates = filtered.map((d) => momentDate(d[dateColumn]));
    const sortedDates = dates.sort((a, b) => a.valueOf() - b.valueOf());

    const { minDate, maxDate } = getWhatIfScenarioMinMaxDate(
      sortedDates[sortedDates.length - 1],
      forecastWindowStart,
      forecastWindowEnd,
      timeUnit
    );

    return {
      minDate,
      maxDate,
    };
  }, [scoringData, targetColumn]);

  const featureOptions = useMemo(() => {
    // Keeping only the non-selected features
    const selectedFeatures = features.map((f) => f.featureName);

    if (!whatIfFeatures) {
      return [];
    }

    return whatIfFeatures
      .filter(({ known_in_advance: knownInAdvance }) => knownInAdvance)
      .filter(
        ({ feature_name: featureName }) =>
          !selectedFeatures.includes(featureName)
      )
      .map(({ feature_name: featureName }) => ({
        key: featureName,
        title: featureName,
      }));
  }, [whatIfFeatures, features]);

  const scenarioFeatures = useMemo(() => {
    return scenario.features.map((feature) => {
      const currentFeature = whatIfFeatures?.find(
        (f) => f.feature_name === feature.featureName
      );

      if (!currentFeature) {
        return {
          ...feature,
          featureOptions: [],
        };
      }

      return {
        ...feature,
        featureOptions: currentFeature?.values || [],
      };
    });
  }, [whatIfFeatures, scenario, minDate, maxDate]);

  const onAddFeature = (featureName: string) => {
    setCurrentScenario({
      ...scenario,
      features: [...features, { featureName, values: [] }],
    });
    setDoesScenarioNeedUpdate(true);
  };

  const onCustomizeInBulkOpen = () => {
    setShowBulkScenarioEditorModal(true);
  };

  const onBulkScenarioEditorConfirm = (customizations: Customizations[]) => {
    const newFeatures = customizations.reduce(
      (acc, { featureName, date, value }) => {
        // Find if the feature already exists in the features array
        const featureIndex = acc.findIndex(
          (f) => f.featureName === featureName
        );

        // If the feature already exists, update its values array
        if (featureIndex !== -1) {
          const feature = acc[featureIndex];

          return [
            ...acc.slice(0, featureIndex),
            {
              ...feature,
              values: [...feature.values, { date, value }],
            },
            ...acc.slice(featureIndex + 1),
          ];
        }

        // If the feature does not exist, add it to the new features array
        return [
          ...acc,
          {
            featureName,
            values: [{ date, value }],
          },
        ];
      },
      features
    );

    setCurrentScenario({
      ...scenario,
      features: newFeatures,
    });

    setShowBulkScenarioEditorModal(false);
    setDoesScenarioNeedUpdate(true);
  };

  const onBulkScenarioEditorDismiss = () => {
    setShowBulkScenarioEditorModal(false);
  };

  const onUpdateScenario = () => {
    if (scenario) {
      updateWhatIfScenario(scenario);
      setDoesScenarioNeedUpdate(false);
    }
  };

  const onDiscardScenario = () => {
    setCurrentScenario(originalScenario as WhatIfScenario);
    setDoesScenarioNeedUpdate(false);
  };

  return (
    <div className='flex flex-col gap-1'>
      <h6 className='text-gray-200'>Scenario customizations</h6>
      <div className='flex flex-col p-4 gap-4 rounded border'>
        <p className='text-gray-400'>
          Add the known-in-advance features you want to customize the values of,
          then specify the date and new value.
        </p>
        <div className='flex gap-2'>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant='ghost' disabled={featureOptions.length === 0}>
                <FontAwesomeIcon icon={faPlus} className='mr-2' />
                Add feature
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className='w-56'>
              {featureOptions.map((option) => (
                <DropdownMenuItem
                  key={option.key}
                  onSelect={() => onAddFeature(option.key as string)}
                >
                  {option.title}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
          <Button variant='ghost' onClick={onCustomizeInBulkOpen}>
            <FontAwesomeIcon icon={faFileLines} className='mr-2' />
            Customize in bulk
          </Button>
        </div>
        <div className='border-t'>
          {scenarioFeatures.map(({ featureOptions, ...rest }, index) => {
            return (
              <ScenarioFeature
                key={index}
                feature={rest}
                featureOptions={featureOptions}
                scenario={scenario}
                minDate={minDate}
                maxDate={maxDate}
                setCurrentScenario={setCurrentScenario}
                setDoesScenarioNeedUpdate={setDoesScenarioNeedUpdate}
              />
            );
          })}
        </div>
        <div className='flex gap-2'>
          <Button onClick={onUpdateScenario} disabled={!doesScenarioNeedUpdate}>
            <FontAwesomeIcon icon={faCheck} className='mr-2' />
            Update scenario
          </Button>
          <Button variant='secondary' onClick={onDiscardScenario}>
            <FontAwesomeIcon icon={faRotateLeft} className='mr-2' />
            Discard changes
          </Button>
        </div>
      </div>
      {showBulkScenarioEditorModal ? (
        <BulkScenarioEditorModal
          onConfirm={onBulkScenarioEditorConfirm}
          onDismiss={onBulkScenarioEditorDismiss}
        />
      ) : null}
    </div>
  );
};

const ScenarioFeature = ({
  feature,
  featureOptions,
  scenario,
  minDate,
  maxDate,
  setCurrentScenario,
  setDoesScenarioNeedUpdate,
}: {
  feature: WhatIfScenarioFeature;
  featureOptions: string[] | number[];
  scenario: WhatIfScenario;
  minDate: Date;
  maxDate: Date;
  setCurrentScenario: (scenario: WhatIfScenario) => void;
  setDoesScenarioNeedUpdate: (value: boolean) => void;
}) => {
  const { featureName, values } = feature;

  const onAddValue = () => {
    setCurrentScenario({
      ...scenario,
      features: [
        ...scenario.features.map((currentFeature) =>
          currentFeature.featureName === featureName
            ? {
                ...currentFeature,
                values: [
                  ...currentFeature.values,
                  {
                    date: minDate,
                    value: 0,
                  },
                ],
              }
            : currentFeature
        ),
      ],
    });
    setDoesScenarioNeedUpdate(true);
  };

  const onRemoveFeature = () => {
    setCurrentScenario({
      ...scenario,
      features: scenario.features.filter((f) => f.featureName !== featureName),
    });
    setDoesScenarioNeedUpdate(true);
  };

  const onValueChange = (index: number, value: number | string) => {
    const features = [...scenario.features];
    const featureIndex = features.findIndex(
      (f) => f.featureName === featureName
    );

    if (featureIndex === -1) {
      setCurrentScenario(scenario);
    }

    const feature = features[featureIndex];
    const values = [...feature.values];
    values[index] = { ...values[index], value };
    features[featureIndex] = { ...feature, values };

    setCurrentScenario({ ...scenario, features });
    setDoesScenarioNeedUpdate(true);
  };

  const onDateChange = (index: number, date: string) => {
    const features = [...scenario.features];
    const featureIndex = features.findIndex(
      (f) => f.featureName === featureName
    );

    if (featureIndex === -1) {
      setCurrentScenario(scenario);
    }

    const feature = features[featureIndex];
    const values = [...feature.values];
    values[index] = { ...values[index], date };
    features[featureIndex] = { ...feature, values };

    setCurrentScenario({ ...scenario, features });
    setDoesScenarioNeedUpdate(true);
  };

  const onRemoveValue = (index: number) => {
    const features = [...scenario.features];
    const featureIndex = features.findIndex(
      (f) => f.featureName === featureName
    );

    if (featureIndex === -1) {
      setCurrentScenario(scenario);
    }

    const feature = features[featureIndex];
    const values = [...feature.values];
    values.splice(index, 1);
    features[featureIndex] = { ...feature, values };

    setCurrentScenario({ ...scenario, features });
    setDoesScenarioNeedUpdate(true);
  };

  const renderHeader = useCallback(() => {
    return (
      <div className='flex items-center gap-2'>
        <span>{featureName}</span>
        {values.length > 0 && (
          <Badge variant='secondary'>{values.length}</Badge>
        )}
      </div>
    );
  }, [feature, values]);

  return (
    <Accordion type='single' collapsible>
      <AccordionItem value={featureName}>
        <AccordionTrigger>{renderHeader()}</AccordionTrigger>
        <AccordionContent>
          <div className='flex flex-col gap-2 pb-4'>
            <Table className='h-full'>
              <TableHeader>
                <TableRow>
                  <TableHead className='w-[300px]'>Date</TableHead>
                  <TableHead>New value</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {feature.values.map(({ date, value }, index) => (
                  <ScenarioFeatureValue
                    key={index}
                    index={index}
                    date={date}
                    value={value}
                    minDate={minDate}
                    maxDate={maxDate}
                    featureOptions={featureOptions}
                    onDateChange={onDateChange}
                    onValueChange={onValueChange}
                    onRemoveValue={onRemoveValue}
                  />
                ))}
              </TableBody>
            </Table>
            <div className='flex gap-2'>
              <Button variant='ghost' onClick={onAddValue}>
                <FontAwesomeIcon icon={faPlus} className='mr-2' />
                Add date
              </Button>
              <Button variant='ghost' onClick={onRemoveFeature}>
                <FontAwesomeIcon icon={faTrashCan} className='mr-2' />
                Remove feature
              </Button>
            </div>
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
};

const ScenarioFeatureValue = ({
  index,
  date,
  value,
  minDate,
  maxDate,
  featureOptions,
  onDateChange,
  onValueChange,
  onRemoveValue,
}: {
  index: number;
  date: string | Date;
  value: number | string;
  minDate: Date;
  maxDate: Date;
  featureOptions: string[] | number[];
  onDateChange: (index: number, date: string) => void;
  onValueChange: (index: number, value: number | string) => void;
  onRemoveValue: (index: number) => void;
}) => {
  const { doesDateContainTime, appSettings } = useContext(AppStateContext);
  const {
    timestep_settings: { timeStep, timeUnit },
  } = appSettings;

  const datePickerTimeConstraints = useMemo(() => {
    if (doesDateContainTime) {
      return getDatePickerTimeConstraints(timeStep, timeUnit);
    }

    return undefined;
  }, [doesDateContainTime, timeStep, timeUnit]);

  const renderInputComponent = useCallback(() => {
    if (featureOptions.length > 0) {
      return (
        <Select
          value={(value as string) || undefined}
          onValueChange={(selectedValue) => {
            onValueChange(index, selectedValue as string);
          }}
        >
          <SelectTrigger className='min-w-[180px] w-full'>
            <SelectValue placeholder='Select a value' />
          </SelectTrigger>
          <SelectContent>
            {featureOptions.map((option) => (
              <SelectItem value={option as string}>{option}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      );
    }

    return (
      <Input
        type='number'
        value={value}
        onChange={(e) => onValueChange(index, e.currentTarget.value)}
      />
    );
  }, [featureOptions, value, onValueChange]);

  return (
    <TableRow>
      <TableCell>
        <DateTimePicker
          value={date}
          startDate={minDate}
          endDate={maxDate}
          timeFormat={doesDateContainTime ? "HH:mm" : false}
          timeConstraints={datePickerTimeConstraints}
          onChange={(date) => onDateChange(index, date as string)}
        />
      </TableCell>
      <TableCell>{renderInputComponent()}</TableCell>
      <TableCell className='text-right'>
        <Button variant='ghost' onClick={() => onRemoveValue(index)}>
          <FontAwesomeIcon icon={faTrashCan} />
        </Button>
      </TableCell>
    </TableRow>
  );
};

export default WhatIfScenarios;
