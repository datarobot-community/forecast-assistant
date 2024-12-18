import { useState, useContext, useMemo } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faArrowUpRightFromSquare } from "@fortawesome/free-solid-svg-icons/faArrowUpRightFromSquare";
import { faArrowsRotate } from "@fortawesome/free-solid-svg-icons/faArrowsRotate";
import { faShareNodes } from "@fortawesome/free-solid-svg-icons/faShareNodes";
import { Button } from "~/components/ui/button";
import ShareModal from "~/components/ShareModal";
import SidebarMenu, {
  type SidebarMenuOptionType,
} from "~/components/ui-custom/SidebarMenu";
import MultiSelectDropdown, {
  MultiSelectDropdownOption,
} from "~/components/ui-custom/MultiSelectDropdown";
import drLogo from "~/assets/dr-logo.svg";
import { ROUTES } from "~/pages/routes";
import calculatePredictions from "~/api/calculatePredictions";
import { AppStateContext, ForecastData } from "~/state/AppState";
import makeLlmRequest from "~/api/makeLlmRequest";

const Sidebar = () => {
  return (
    <div className='flex flex-col gap-6 p-6 flex-shrink-0 h-full w-[330px] overflow-y-auto border-r'>
      <SidebarHeader />
      <Divider />
      <AppSections />
      <Divider />
      <ForecastSettings />
      <Divider />
      <BehindTheScenes />
    </div>
  );
};

const Divider = () => {
  return <hr className='border-t' />;
};

const SidebarHeader = () => {
  const { appSettings } = useContext(AppStateContext);
  const [isShareModalOpen, setIsShareModalOpen] = useState(false);

  return (
    <div className='flex flex-col gap-4'>
      <img src={drLogo} alt='DataRobot' className='w-[130px]' />
      <div className='flex flex-col items-start gap-2'>
        <h4 className='text-lg font-medium text-white'>
          {appSettings.page_title || "Forecasting App"}
        </h4>
        <p className='mb-2 leading-5 text-gray-400'>
          {appSettings.page_description}
        </p>
        <Button
          onClick={() => {
            setIsShareModalOpen(true);
          }}
          variant='outline'
        >
          <FontAwesomeIcon icon={faShareNodes} className='mr-2' />
          Share
        </Button>

        {isShareModalOpen ? (
          <ShareModal onDismiss={() => setIsShareModalOpen(false)} />
        ) : null}
      </div>
    </div>
  );
};

const AppSections = () => {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { appSettings } = useContext(AppStateContext);
  const { what_if_features: whatIfFeatures } = appSettings;
  const [activeKey, setActiveKey] = useState<string>(
    pathname === ROUTES.WHAT_IF_SCENARIOS ? "what-if-scenarios" : "explanations"
  );

  const isWhatIfScenariosAvailable = useMemo(() => {
    if (!whatIfFeatures) return false;

    return whatIfFeatures.some((feature) => feature.known_in_advance);
  }, [whatIfFeatures]);

  const options: SidebarMenuOptionType[] = [
    {
      key: "explanations",
      name: "Explanations",
      active: activeKey === "explanations",
      onClick: () => {
        navigate(ROUTES.EXPLANATIONS);
        setActiveKey("explanations");
      },
    },
    {
      key: "what-if-scenarios",
      name: "What-if Scenarios",
      active: activeKey === "what-if-scenarios",
      disabled: !isWhatIfScenariosAvailable,
      onClick: () => {
        if (!isWhatIfScenariosAvailable) {
          return;
        }
        navigate(ROUTES.WHAT_IF_SCENARIOS);
        setActiveKey("what-if-scenarios");
      },
    },
  ];

  return (
    <div className='flex flex-col gap-2'>
      <h6 className='font-medium text-gray-200'>App sections</h6>
      <SidebarMenu options={options} activeKey={activeKey} />
    </div>
  );
};

const ForecastSettings = () => {
  const {
    appSettings,
    scoringData,
    forecastDataLoading,
    filterOptions: filterOptionsObject,
    filters,
    inputDateFormat,
    outputDateFormat,
    setFilters,
    setForecastData,
    setForecastDataLoading,
    setNaturalLanguageSummary,
    setNaturalLanguageSummaryLoading,
  } = useContext(AppStateContext);
  const { datetime_partition_column: dateColumn } = appSettings;
  const { pathname } = useLocation();

  const filterOptions = useMemo(
    () =>
      Object.keys(filterOptionsObject).map((key) => filterOptionsObject[key]),
    [filterOptionsObject]
  );

  const inputsDisabled = useMemo(() => {
    return pathname.includes(ROUTES.WHAT_IF_SCENARIOS) || forecastDataLoading;
  }, [pathname, forecastDataLoading]);

  const getSummary = async (forecastData: ForecastData[]) => {
    if (!forecastData.length) return;

    setNaturalLanguageSummaryLoading(true);
    try {
      const summary = await makeLlmRequest(forecastData);
      setNaturalLanguageSummary(summary.summary_body);
    } catch (error) {
      throw new Error("Error fetching summary");
    } finally {
      setNaturalLanguageSummaryLoading(false);
    }
  };

  const onCalculatePredictions = async () => {
    try {
      setNaturalLanguageSummary("");
      setForecastDataLoading(true);
      const { data, forecastSeriesIdsCount } = await calculatePredictions({
        scoringData,
        dateColumn,
        outputDateFormat,
        inputDateFormat,
      });
      setForecastData(data, forecastSeriesIdsCount);
      getSummary(data);
    } catch (error) {
      console.error(error);
    }
    setForecastDataLoading(false);
  };

  const onFilterOptionSelect = (filterName: string, selectedOption: string) => {
    const currentFilter = filters[filterName] || [];
    if (currentFilter.includes(selectedOption)) {
      return;
    }

    setFilters({
      ...filters,
      [filterName]: [...currentFilter, selectedOption],
    });
  };

  const onFilterOptionDelete = (filterName: string, deletedOption: string) => {
    const currentFilter = filters[filterName] || [];
    const updatedFilter = currentFilter.filter(
      (option) => option !== deletedOption
    );

    setFilters({
      ...filters,
      [filterName]: updatedFilter,
    });
  };

  return (
    <div className='flex flex-col gap-4'>
      <div>
        <h6 className='font-medium text-gray-200'>Forecast settings</h6>
        <p className='leading-5 text-gray-400'>
          Configure the forecast settings to see how the forecast changes.
        </p>
      </div>
      {filterOptions.map((filter) => {
        const items = filters[filter.name] || [];
        return (
          <MultiSelectDropdown
            key={filter.name}
            label={filter.displayName}
            placeholder='All options selected'
            disabled={inputsDisabled}
            options={filter.options.map((option) => ({
              id: option,
              title: option,
            }))}
            items={items}
            onSelect={(selectedOption: MultiSelectDropdownOption) => {
              const isOptionSelected = items.includes(selectedOption.id);

              if (!isOptionSelected) {
                onFilterOptionSelect(filter.name, selectedOption.id);
              } else {
                onFilterOptionDelete(filter.name, selectedOption.id);
              }
            }}
          />
        );
      })}

      <div>
        <Button
          variant='outline'
          onClick={onCalculatePredictions}
          disabled={forecastDataLoading}
        >
          <FontAwesomeIcon icon={faArrowsRotate} className='mr-2' />
          Update forecast
        </Button>
      </div>
    </div>
  );
};

const BehindTheScenes = () => {
  const { appSettings, runtimeAttributes } = useContext(AppStateContext);
  const { target, scoring_dataset_id, model_name } = appSettings;
  const {
    app_creator_email: created_by,
    app_latest_created_date: created_at,
    app_urls,
  } = runtimeAttributes;
  const { dataset: dataset_url, model: model_url } = app_urls || {};

  const createdDate = useMemo(
    () =>
      new Date(created_at).toLocaleDateString("en-US", {
        month: "long",
        day: "numeric",
        year: "numeric",
      }),
    []
  );

  return (
    <div className='flex flex-col gap-4'>
      <div className='flex flex-col gap-1'>
        <h6 className='text-muted-foreground'>App created</h6>
        <p className='text-gray-100'>
          {createdDate}
          <br />
          by {created_by}
        </p>
      </div>
      <div className='flex flex-col gap-1'>
        <h6 className='text-muted-foreground'>Prediction dataset</h6>
        <a
          className='flex items-center gap-1 text-gray-100'
          href={dataset_url}
          target='_blank'
        >
          {scoring_dataset_id || "Scoring dataset"}
          <FontAwesomeIcon icon={faArrowUpRightFromSquare} />
        </a>
      </div>
      <div className='flex flex-col gap-1'>
        <h6 className='text-muted-foreground'>Target feature</h6>
        <p className='text-gray-100'>{target}</p>
      </div>
      <div className='flex flex-col gap-1'>
        <h6 className='text-muted-foreground'>Model</h6>
        <a
          className='flex items-center gap-1 text-gray-100'
          href={model_url}
          target='_blank'
        >
          <span className='truncate' title={model_name}>
            {model_name}
          </span>
          <FontAwesomeIcon icon={faArrowUpRightFromSquare} />
        </a>
      </div>
    </div>
  );
};

export default Sidebar;
