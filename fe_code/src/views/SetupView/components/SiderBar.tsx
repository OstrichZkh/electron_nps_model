import React from "react";
import styled from "styled-components";
import type { MenuProps } from "antd";
import { Menu } from "antd";
import {
  AppstoreOutlined,
  MailOutlined,
  SettingOutlined,
} from "@ant-design/icons";
type MenuItem = Required<MenuProps>["items"][number];
const SiderBarBox = styled.div`
  height: 100vh;
  width: 12rem;
  background-color: rgb(244, 245, 247);
`;
function getItem(
  label: React.ReactNode,
  key: React.Key,
  icon?: React.ReactNode,
  children?: MenuItem[],
  type?: "group"
): MenuItem {
  return {
    key,
    icon,
    children,
    label,
    type,
  } as MenuItem;
}

const items: MenuProps["items"] = [
  getItem("数据准备", "sub1", <AppstoreOutlined />, [
    getItem("模拟期准备", "1"),
    getItem("降雨数据", "2"),
    getItem("土地利用类型", "3"),
    getItem("土壤类型", "4"),
    getItem("DEM数据", "5"),
    getItem("RUSLE数据", "6"),
  ]),
  { type: "divider" },
  getItem("面源污染模拟", "sub2", <AppstoreOutlined />, [
    getItem("水土流失情况", "rusle"),
    getItem("模型参数设置", "parameters", null, [
      getItem("农业措施设置", "fert"),
      getItem("率定参数设置", "calib"),
      getItem("NSGA参数设置", "nsga"),
    ]),
    getItem("模型运行", "model"),
  ]),
];
function SiderBar() {
  let menuClick: MenuProps["onClick"] = function (e): void {
    console.log(e);
  };
  return (
    <SiderBarBox>
      <Menu
        onClick={menuClick}
        items={items}
        style={{ width: "12rem" }}
        defaultSelectedKeys={["1"]}
        defaultOpenKeys={["sub1"]}
        mode="inline"
      />
    </SiderBarBox>
  );
}

export default SiderBar;
