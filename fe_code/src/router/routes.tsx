import ProjectView from "../views/ProjectView";
import SetupView from "../views/SetupView";
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
    path: "setup",
    component: () => <Navigate to="setup/simrange" />,
  },
  {
    path: "setup/simrange",
    name: "simrange",
    component: lazy(
      () => import(/* webpackChunkName:"setup" */ "../views/SimRangeView")
    ),
    meta: {},
  },
  {
    path: "setup/rainfall",
    name: "rainfall",
    component: lazy(
      () => import(/* webpackChunkName:"setup" */ "../views/RainfallView")
    ),
    meta: {},
  },
  {
    path: "setup/landuse",
    name: "landuse",
    component: lazy(
      () => import(/* webpackChunkName:"setup" */ "../views/LanduseView")
    ),
    meta: {},
  },

  {
    path: "setup/dem",
    name: "dem",
    component: lazy(
      () => import(/* webpackChunkName:"setup" */ "../views/DemView")
    ),
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
