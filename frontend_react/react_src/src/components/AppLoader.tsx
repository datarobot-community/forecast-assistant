import drIcon from "~/assets/dr-icon.svg";

const AppLoader = () => {
  return (
    <div className='flex flex-col gap-4 items-center justify-center h-screen w-screen'>
      <img src={drIcon} alt='DataRobot' />
      <p className='mb-2 text-gray-400 animate-pulse'>Loading data...</p>
    </div>
  );
};

export default AppLoader;
