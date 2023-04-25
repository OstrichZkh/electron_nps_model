import React, { useState } from "react";
import styled from "styled-components";
import type { MenuProps } from "antd";
import { Menu } from "antd";
import { SettingOutlined } from "@ant-design/icons";
import { useNavigate, useLocation } from "react-router-dom";

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
  getItem("数据准备", "sub1", <SettingOutlined />, [
    getItem("模拟期准备", "simrange"),
    getItem("降雨数据", "rainfall"),
    getItem("土地利用类型", "landuse"),
    getItem("土壤类型", "soiltype"),
    getItem("DEM数据", "dem"),
    getItem("RUSLE数据", "rusledata"),
  ]),
  { type: "divider" },
  getItem("面源污染模拟", "sub2", <SettingOutlined />, [
    getItem("水土流失情况", "ruslecal"),
    getItem("模型参数设置", "parameters", null, [
      getItem("农业措施设置", "fert"),
      getItem("率定参数设置", "calib"),
      getItem("NSGA参数设置", "nsga"),
    ]),
    getItem("模型运行", "model"),
  ]),
];
function SiderBar() {
  const navigate = useNavigate();
  let menuClick: MenuProps["onClick"] = function (e): void {
    navigate(`/setup/${e.key}`, { replace: true });
  };

  let initSelect: string = "";
  // 设置只能有一个展开项
  const [openKeys, setOpenKeys] = useState([initSelect]);

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

export default React.memo(SiderBar);
