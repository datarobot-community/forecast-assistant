import { useState } from "react";
import moment, { Moment } from "moment";
import Datetime from "react-datetime";
import { Calendar } from "lucide-react";
import { Input } from "~/components/ui/input";
import "./DateTimePicker.css";

type TimeConstraint = {
  min: number;
  max: number;
  step: number;
};

type TimeConstraints = {
  hours?: TimeConstraint;
  minutes?: TimeConstraint;
  seconds?: TimeConstraint;
  milliseconds?: TimeConstraint;
};

type Props = {
  value: Date | string;
  inputProps?: {
    disabled: boolean;
  };
  startDate?: Date | string;
  endDate?: Date | string;
  timeFormat: string | false;
  timeConstraints?: TimeConstraints;
  onChange: (value: string | Moment) => void;
};

const DateTimePicker = ({
  value,
  inputProps,
  startDate,
  endDate,
  timeFormat,
  timeConstraints,
  onChange,
}: Props) => {
  const [isOpen, setIsOpen] = useState(false);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const renderInput = (props: any, openCalendar: any) => {
    const handleFocus = () => {
      openCalendar();
      setIsOpen(true);
    };

    return (
      <div className='relative'>
        <Input {...props} onFocus={handleFocus} />
        <Calendar className='absolute right-3 top-2 w-4 text-muted-foreground' />
      </div>
    );
  };

  // eslint-disable-next-line @typescript-eslint/ban-types
  const renderView = (viewMode: string, renderCalendar: Function) => {
    if (!isOpen) {
      return null as unknown as JSX.Element;
    }

    return (
      <div
        className='flex items-center justify-center fixed inset-0 z-50 bg-black/80  animate-in fade-in-0'
        onClick={(e: React.MouseEvent<HTMLDivElement>) => {
          if (e.target === e.currentTarget) {
            setIsOpen(false);
          }
        }}
      >
        <div className='flex flex-col gap-2 p-2 mt-1 bg-popover border border-border rounded-md shadow-md z-50 w-[300px]'>
          {renderCalendar()}
          <div className='flex px-3 font-thin text-xs text-center text-gray-400'>
            After selecting the date, click outside to close the calendar
          </div>
        </div>
      </div>
    );
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const isDateEnabled = (currentDate: any) => {
    if (!startDate || !endDate) {
      return true;
    }

    return (
      !currentDate.endOf("day").isBefore(moment(startDate).startOf("day")) &&
      !currentDate.startOf("day").isAfter(moment(endDate).endOf("day"))
    );
  };

  return (
    <Datetime
      className='w-[250px]'
      value={value}
      open={isOpen}
      inputProps={inputProps}
      timeFormat={timeFormat}
      timeConstraints={timeConstraints}
      isValidDate={isDateEnabled}
      renderInput={renderInput}
      renderView={renderView}
      onChange={onChange}
    />
  );
};

export default DateTimePicker;
