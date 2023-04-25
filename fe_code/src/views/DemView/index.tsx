import React, { useState, useEffect } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import FileImporter from "../../components/FileImporter";
import { useSelector, useDispatch } from "react-redux";
import * as echarts from "echarts";

const LanduseViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;
function DemView() {
  const dispatch = useDispatch();
  let { curProjectInfo } = useSelector((state) => state.dataManagementReducer);
  let [echartsOptions, setEchartsOptions]: [any, any] = useState();
  useEffect(() => {
    if (curProjectInfo.DEM.counts) {
      const { DEM: demArr, count: countArr } = curProjectInfo.DEM.counts;
      let myChart = echarts.init(
        document.querySelector(".echarts-DEM") as HTMLElement
      );
      window.onresize = function () {
        myChart.resize();
      };
      myChart.setOption({
        title: {
          text: "DEM分布情况",
          left: "center",
          textStyle: {
            fontSize: 20,
          },
          padding: [20, 0, 0, 0],
        },
        xAxis: {
          type: "category",
          data: demArr,
        },
        yAxis: {},
        series: [
          {
            name: "数量",
            type: "bar",
            data: countArr,
          },
        ],
      });
    }
  }, [JSON.stringify(curProjectInfo.DEM)]);

  return (
    <LanduseViewBox>
      <Title title="DEM数据" />
      <FileImporter type="DEM" svg="" />
      <div
        style={{
          height: "30rem",
          width: "130rem",
          margin: "1rem",
        }}
        className="echarts-DEM"
      ></div>
    </LanduseViewBox>
  );
}

export default DemView;
