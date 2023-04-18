import routes from "./routes.tsx";
import { Suspense } from "react";
import {
  Routes,
  Route,
  useNavigate,
  useLocation,
  useParams,
  useSearchParams,
} from "react-router-dom";
interface Routes {
  path: string;
  name?: string;
  component: Function;
  meta?: object;
  children?: Routes[];
}
// 统一渲染组件，可以做一些特殊处理
const Element = function (props: Routes) {
  let { component: Component } = props;
  // 获取路由信息
  let navigate = useNavigate(),
    location = useLocation(),
    params = useParams(),
    [usp] = useSearchParams();
  return (
    <Component
      navigate={navigate}
      params={params}
      location={location}
      usp={usp}
    ></Component>
  );
};

// 递归创建Routes
const createRoute = function (routes: Routes[]) {
  return (
    <>
      {routes.map((item, index) => {
        const { path, children } = item;
        return (
          <Route path={path} key={index} element={<Element {...item} />}>
            {Array.isArray(children) && createRoute(children)}
          </Route>
        );
      })}
    </>
  );
};

export default function RouterView() {
  return (
    <Suspense fallback={<>正在加载中...</>}>
      <Routes>{createRoute(routes)}</Routes>
    </Suspense>
  );
}

// 创建withRouter
export const withRouter = function withRouter(Component: Function) {
  return function HOC(props: object) {
    let navigate = useNavigate(),
      location = useLocation(),
      params = useParams(),
      [usp] = useSearchParams();
    return (
      <Component
        navigate={navigate}
        params={params}
        location={location}
        usp={usp}
        {...props}
      ></Component>
    );
  };
};
