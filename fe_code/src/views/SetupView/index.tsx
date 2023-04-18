import React from "react";
import SiderBar from "./components/SiderBar";
import { Outlet } from "react-router-dom";

function SetupView() {
  return (
    <div style={{ display: "flex" }}>
      <SiderBar />
      <Outlet />
    </div>
  );
}

export default React.memo(SetupView);
