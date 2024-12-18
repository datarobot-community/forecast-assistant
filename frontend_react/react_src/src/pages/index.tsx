import { Route, Routes } from "react-router-dom";
import Explanations from "./Explanations";
import WhatIfScenarios from "./WhatIfScenarios";
import { ROUTES } from "./routes";

const Pages = () => {
  return (
    <div className='w-full h-full overflow-y-auto'>
      <Routes>
        <Route path={ROUTES.WHAT_IF_SCENARIOS} element={<WhatIfScenarios />} />
        <Route path='*' element={<Explanations />} />
      </Routes>
    </div>
  );
};

export default Pages;
