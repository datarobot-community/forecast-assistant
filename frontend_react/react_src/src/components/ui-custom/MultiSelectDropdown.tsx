import clsx from "clsx";
import { useLayoutEffect, useMemo, useRef, useState } from "react";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "~/components/ui/dropdown-menu";
import { Label } from "~/components/ui/label";

export type MultiSelectDropdownOption = {
  id: string;
  title: string;
};

type MultiSelectDropdownProps = {
  label?: string;
  placeholder?: string;
  disabled?: boolean;
  options: MultiSelectDropdownOption[];
  items: string[];
  onSelect: (selectedOption: MultiSelectDropdownOption) => void;
};

const MultiSelectDropdown = ({
  label,
  placeholder,
  disabled,
  options,
  items,
  onSelect,
}: MultiSelectDropdownProps) => {
  const triggerRef = useRef<HTMLDivElement>(null);
  const [menuWidth, setMenuWidth] = useState<number | "auto">("auto");

  const dropdownOptions = useMemo(() => {
    return options.map((option) => ({
      id: option.id,
      title: option.title,
      checked: items.includes(option.id),
    }));
  }, [options, items]);

  const placeholderText = useMemo(() => {
    if (!items.length) {
      return placeholder;
    }

    if (items.length <= 2) {
      return items.join(", ");
    }

    return `${items.length} options selected`;
  }, [items, placeholder]);

  useLayoutEffect(() => {
    if (!triggerRef.current) {
      return;
    }

    const { width } = triggerRef.current.getBoundingClientRect();
    setMenuWidth(width);
  }, []);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild disabled={disabled}>
        <div
          className={clsx("flex flex-col items-start gap-1.5", {
            "cursor-pointer": !disabled,
            "cursor-not-allowed opacity-50": disabled,
          })}
          ref={triggerRef}
        >
          <Label>{label}</Label>
          <div
            className={clsx(
              "flex px-3 py-2 h-10 w-full rounded-md border border-input bg-background text-sm transition-colors",
              {
                "hover:bg-muted/90": !disabled,
              }
            )}
          >
            {placeholderText}
          </div>
        </div>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        style={{
          width: menuWidth,
          minWidth: "60px",
        }}
      >
        {dropdownOptions.map((option) => (
          <DropdownMenuCheckboxItem
            key={option.id}
            checked={option.checked}
            disabled={disabled}
            onCheckedChange={() => onSelect(option)}
          >
            {option.title}
          </DropdownMenuCheckboxItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default MultiSelectDropdown;
