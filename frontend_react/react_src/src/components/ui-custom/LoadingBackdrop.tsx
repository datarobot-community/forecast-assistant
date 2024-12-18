import Spinner from "./Spinner";

const LoadingBackdrop = ({ message }: { message: string }) => {
  return (
    <div className='flex items-center gap-2 px-6 py-4 rounded-lg bg-black/70'>
      <Spinner />
      <span>{message}</span>
    </div>
  );
};

export default LoadingBackdrop;
