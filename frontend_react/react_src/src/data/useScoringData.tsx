import { useEffect, useMemo, useState } from "react";
import { ScoringData, FilterableCategory } from "~/state/AppState";
import { type ConfigFilterableCategory } from "~/data/useConfigs";
import { formatDateString } from "~/helpers";
import getScoringData from "~/api/getScoringData";

type Filters = {
  [key: string]: string[];
};

type Props = {
  filters: Filters;
  filterableCategories: ConfigFilterableCategory[];
  dateColumn: string;
  inputDateFormat: string;
};

type ReturnType = {
  data: ScoringData[];
  loading: boolean;
  filterOptions: { [key: string]: FilterableCategory };
  datasetColumns: string[];
};

const useScoringData = ({
  filters = {},
  filterableCategories = [],
  dateColumn,
  inputDateFormat,
}: Props): ReturnType => {
  const [fetchedData, setFetchedData] = useState<ScoringData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await getScoringData(filters);

        // Format the date string
        const newData = data.map((d) => {
          return {
            ...d,
            [dateColumn]: formatDateString(
              d[dateColumn],
              inputDateFormat
            ) as string,
          };
        });

        setFetchedData(newData);
      } catch (error) {
        console.error("Error fetching configs", error);
      }
      setLoading(false);
    };
    if (dateColumn && inputDateFormat) {
      fetchData();
    }
  }, [dateColumn, inputDateFormat]);

  const { allData, filterOptions, datasetColumns } = useMemo(() => {
    if (!fetchedData.length) {
      return { allData: [], filterOptions: {}, datasetColumns: [] };
    }

    // Filter options
    const filterOptions: { [key: string]: FilterableCategory } = {};
    filterableCategories.forEach((category) => {
      const options = Array.from(
        new Set(fetchedData.map((d) => d[category.column_name]))
      );

      filterOptions[category.column_name] = {
        name: category.column_name,
        displayName: category.display_name,
        options,
      };
    });

    // Dataset columns
    const datasetColumns =
      fetchedData.length > 0 ? Object.keys(fetchedData[0]) : [];

    return { allData: fetchedData, filterOptions, datasetColumns };
  }, [fetchedData, filterableCategories]);

  // Filtered Data
  const filteredData = useMemo(() => {
    const filtered = allData.filter((d) => {
      return Object.keys(filters).every((key) => {
        const keyFilters = filters[key];
        // Check if the current data record has any of the selected filters
        if (keyFilters.length > 0) {
          return keyFilters.includes(d[key]);
        }

        // If no filters are selected, return all data
        return true;
      });
    });

    return filtered;
  }, [allData, filters]);

  return { data: filteredData, loading, filterOptions, datasetColumns };
};

export default useScoringData;
