import React from "react";
import SiderBar from "./components/SiderBar";
import type { MenuProps } from "antd";
import { Menu } from "antd";
type MenuItem = Required<MenuProps>["items"][number];

function SetupView() {
  return (
    <div>
      <SiderBar />
    </div>
  );
}

export default SetupView;
