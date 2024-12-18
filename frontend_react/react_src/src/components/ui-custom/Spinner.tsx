import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faCircleNotch } from "@fortawesome/free-solid-svg-icons/faCircleNotch";
import { cn } from "~/lib/utils";

const Spinner = ({ className }: { className?: string }) => {
  return (
    <FontAwesomeIcon
      icon={faCircleNotch}
      className={cn("text-white", className)}
      spin
    />
  );
};

export default Spinner;
