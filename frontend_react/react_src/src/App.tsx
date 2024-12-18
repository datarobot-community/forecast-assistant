import { useContext } from "react";
import { Toaster } from "~/components/ui/toaster";
import Sidebar from "~/components/Sidebar";
import AppLoader from "~/components/AppLoader";
import Pages from "~/pages";
import { AppStateContext, AppStateProvider } from "~/state/AppState";

function App() {
  return (
    <AppStateProvider>
      <MainContainer />
      <Toaster />
    </AppStateProvider>
  );
}

function MainContainer() {
  const { appSettings, configsLoading, scoringDataLoading } =
    useContext(AppStateContext);

  if (configsLoading || scoringDataLoading) {
    return <AppLoader />;
  }

  if (Object.keys(appSettings || {}).length === 0) {
    return <ConfigsNotFound />;
  }

  return (
    <div className='flex h-full'>
      <Sidebar />
      <Pages />
    </div>
  );
}

const ConfigsNotFound = () => {
  return (
    <div className='flex flex-col gap-1 p-4'>
      <h4 className='text-lg font-semibold'>Configs not found</h4>
      <p className='text-gray-400'>Please reload the page or contact support</p>
    </div>
  );
};

export default App;
