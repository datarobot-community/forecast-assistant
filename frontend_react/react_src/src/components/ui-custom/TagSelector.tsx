import { useMemo } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faTimes } from "@fortawesome/free-solid-svg-icons";

export type TagOption = {
  id: string;
  title: string;
};

type Props = {
  placeholder: string;
  options: TagOption[];
  selectedItems: TagOption[];
  onSearch: (e: string) => void;
  onSelect: (item: TagOption) => void;
  onDelete: (id: string) => void;
};

const TagSelector = ({
  placeholder,
  options,
  selectedItems,
  onSearch,
  onSelect,
  onDelete,
}: Props) => {
  const placeholderText = useMemo(() => {
    return selectedItems.length > 0 ? "" : placeholder;
  }, [placeholder, selectedItems]);

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && event.currentTarget.value !== "") {
      const item = options.find(
        (option) => option.title === event.currentTarget.value
      );
      if (item) {
        onSelect(item);
        event.currentTarget.value = "";
      }
      return;
    }
    if (event.key === "Backspace" && event.currentTarget.value === "") {
      onDelete(selectedItems[selectedItems.length - 1].id);
    }
  };

  return (
    <div className='flex flex-wrap gap-1 p-3 w-full rounded-md border border-input bg-background text-sm'>
      {selectedItems.map((item, index) => (
        <TagItem
          key={`${item.id}-${index}`}
          title={item.title}
          onDelete={() => onDelete(item.id)}
        />
      ))}
      <input
        className='flex-1 bg-transparent focus:outline-none'
        placeholder={placeholderText}
        onKeyDown={handleKeyDown}
        onChange={(e) => onSearch(e.target.value)}
      />
    </div>
  );
};

const TagItem = ({
  title,
  onDelete,
}: {
  title: string;
  onDelete: () => void;
}) => {
  return (
    <div className='flex items-center gap-2 bg-muted h-6 px-2 rounded-md border border-inpu text-xs'>
      <span>{title}</span>
      <span onClick={onDelete} aria-label={`Remove ${title}`}>
        <FontAwesomeIcon icon={faTimes} />
      </span>
    </div>
  );
};

export default TagSelector;
