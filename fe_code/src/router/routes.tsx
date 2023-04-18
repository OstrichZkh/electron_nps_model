import ProjectView from "../views/ProjectView";
import SetupView from "../views/SetupView";
import RainfallView from "../views/RainfallView";
import SimRangeView from "../views/SimRangeView";
import LanduseView from "../views/LanduseView";
import SoiltypeView from "../views/SoiltypeView";
import DemView from "../views/DemView";
import RusledataView from "../views/RusleDataView";
import { lazy } from "react";
import { Navigate } from "react-router-dom";

interface Routes {
  path: string;
  name?: string;
  component: Function;
  meta?: object;
  children?: Routes[];
}

const setupRoutes: Routes[] = [
  {
    path: "/setup",
    component: () => <Navigate to="/setup/simrange" />,
  },
  {
    path: "/setup/simrange",
    name: "simrange",
    component: SimRangeView,
    meta: {},
  },
  {
    path: "/setup/rainfall",
    name: "rainfall",
    component: RainfallView,
    meta: {},
  },
  {
    path: "/setup/landuse",
    name: "landuse",
    component: LanduseView,
    meta: {},
  },
  {
    path: "/setup/soiltype",
    name: "soiltype",
    component: SoiltypeView,
    meta: {},
  },
  {
    path: "/setup/dem",
    name: "dem",
    component: DemView,
    meta: {},
  },
  {
    path: "/setup/rusledata",
    name: "rusledata",
    component: RusledataView,
    meta: {},
  },
];

const routes: Routes[] = [
  {
    path: "/",
    name: "ProjectView",
    component: ProjectView,
    meta: {},
    children: [],
  },
  {
    path: "/setup",
    name: "SetupView",
    component: SetupView,
    meta: {},
    children: setupRoutes,
  },
];

export default routes;
