import { useMemo, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faChartLine } from "@fortawesome/free-solid-svg-icons/faChartLine";
import { faTable } from "@fortawesome/free-solid-svg-icons/faTable";
import { Tabs, TabsList, TabsTrigger } from "~/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "~/components/ui/dialog";
import { Button } from "~/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "~/components/ui/select";
import { Label } from "~/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "~/components/ui/table";
import { FormattedXEMPFeature } from "~/helpers";
import XEMPModalLineChart from "./XEMPModalLineChart";

type Props = {
  allFeatures: FormattedXEMPFeature[];
  selectedFeature: string;
  setSelectedFeature: (feature: string | null) => void;
};

const XEMPFeaturesModal = ({
  allFeatures,
  selectedFeature,
  setSelectedFeature,
}: Props) => {
  const [activeTab, setActiveTab] = useState("trends");

  const currentFeature = useMemo(
    () => allFeatures.find((f) => f.feature === selectedFeature),
    [allFeatures, selectedFeature]
  );

  const onClose = () => {
    setSelectedFeature(null);
  };

  if (!currentFeature) {
    return null;
  }

  return (
    <Dialog
      open
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          onClose();
        }
      }}
    >
      <DialogContent className='flex flex-col sm:max-w-[720px] max-h-[90vh] overflow-hidden'>
        <DialogHeader>
          <DialogTitle>XEMP over time</DialogTitle>
          <DialogDescription>
            See how the values of the selected feature over time influence the
            forecast, based on XEMP.
          </DialogDescription>
        </DialogHeader>
        <div className='flex flex-col gap-4 flex-grow overflow-y-auto'>
          <div className='flex flex-col gap-1.5'>
            <Label htmlFor='feature-select'>Feature</Label>
            <Select
              value={selectedFeature}
              onValueChange={(selectedValue) => {
                setSelectedFeature(selectedValue);
              }}
            >
              <SelectTrigger id='feature-select'>
                <SelectValue placeholder='Select a value' />
              </SelectTrigger>
              <SelectContent>
                {allFeatures.map(({ feature }) => (
                  <SelectItem key={feature} value={feature as string}>
                    {feature}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <Tabs
            defaultValue='trends'
            className='flex flex-col gap-4 items-start'
            onValueChange={(value) => setActiveTab(value)}
          >
            <TabsList>
              <TabsTrigger value='trends'>
                <FontAwesomeIcon className='mr-2' icon={faChartLine} />
                Trends
              </TabsTrigger>
              <TabsTrigger value='raw-values'>
                <FontAwesomeIcon className='mr-2' icon={faTable} />
                Raw values
              </TabsTrigger>
            </TabsList>
          </Tabs>
          {activeTab === "trends" ? (
            <Trends currentFeature={currentFeature} />
          ) : (
            <RawValues currentFeature={currentFeature} />
          )}
        </div>
        <DialogFooter>
          <Button variant='outline' onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

const Trends = ({
  currentFeature,
}: {
  currentFeature: FormattedXEMPFeature;
}) => {
  return (
    <div className='flex flex-col gap-2'>
      <XEMPModalLineChart
        data={currentFeature.featureRecords}
        dataType='forecast'
      />
      <XEMPModalLineChart
        data={currentFeature.featureRecords}
        dataType='xempValue'
      />
      <XEMPModalLineChart
        data={currentFeature.featureRecords}
        dataType='featureValue'
        showBottomAxis
      />
    </div>
  );
};

const RawValues = ({
  currentFeature,
}: {
  currentFeature: FormattedXEMPFeature;
}) => {
  const tableRows = useMemo(() => {
    return currentFeature.featureRecords.map((record, index) => {
      return (
        <TableRow key={index}>
          <TableCell>
            {new Date(record.date).toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            })}
          </TableCell>
          <TableCell>{record.prediction || "-"}</TableCell>
          <TableCell>{record.strength || "-"}</TableCell>
          <TableCell>{record.featureValue || "-"}</TableCell>
        </TableRow>
      );
    });
  }, [currentFeature]);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Forecast distance</TableHead>
          <TableHead>Forecast value</TableHead>
          <TableHead>XEMP value</TableHead>
          <TableHead>Feature value</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>{tableRows}</TableBody>
    </Table>
  );
};

export default XEMPFeaturesModal;
