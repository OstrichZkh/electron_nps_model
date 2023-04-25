import ProjectView from "../views/ProjectView";
import SetupView from "../views/SetupView";
import RainfallView from "../views/RainfallView";
import SimRangeView from "../views/SimRangeView";
import LanduseView from "../views/LanduseView";
import SoiltypeView from "../views/SoiltypeView";
import DemView from "../views/DemView";
import RusledataView from "../views/RusleDataView";
import RusleCalView from "../views/RusleCalView";
import FertView from "../views/FertView";
import ParasView from "../views/ParasView";
import NsgaView from "../views/NsgaView";
import ModelRunView from "../views/ModelRunView";
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
  {
    path: "/setup/ruslecal",
    name: "ruslecal",
    component: RusleCalView,
    meta: {},
  },
  {
    path: "/setup/fert",
    name: "fert",
    component: FertView,
    meta: {},
  },
  {
    path: "/setup/calib",
    name: "calib",
    component: ParasView,
    meta: {},
  },
  {
    path: "/setup/nsga",
    name: "nsga",
    component: NsgaView,
    meta: {},
  },
  {
    path: "/setup/model",
    name: "model",
    component: ModelRunView,
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
