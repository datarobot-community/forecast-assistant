import { cn } from "~/lib/utils";

export type SidebarMenuOptionType = {
  key: string;
  name: string;
  active?: boolean;
  disabled?: boolean;
  onClick: () => void;
};

type Props = {
  options: SidebarMenuOptionType[];
  activeKey?: string;
};

const SidebarMenu = ({ options }: Props) => {
  return (
    <div className='flex flex-col gap-2'>
      {options.map((option) => (
        <SidebarMenuOption
          key={option.key}
          name={option.name}
          active={option.active}
          disabled={option.disabled}
          onClick={option.onClick}
        />
      ))}
    </div>
  );
};

const SidebarMenuOption = ({
  name,
  active,
  disabled,
  onClick,
}: SidebarMenuOptionType) => {
  return (
    <div
      className={cn(
        "flex gap-2 px-3 py-2 rounded border-l-2 border-transparent overflow-hidden transition-colors cursor-pointer hover:bg-muted/90",
        {
          "rounded-l-none border-l-2 border-primary bg-muted": active,
          "opacity-50 cursor-not-allowed": disabled,
        }
      )}
      onClick={!disabled ? onClick : () => null}
    >
      <div className='break-words text-gray-200' title={name}>
        {name}
      </div>
    </div>
  );
};

export default SidebarMenu;
