import React, { useState, useEffect, useReducer } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import FileImporter from "../../components/FileImporter";
import * as echarts from "echarts";
import { useSelector, useDispatch } from "react-redux";

const RainfallViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;

function RainfallView() {
  let { curProjectInfo } = useSelector((state) => state.dataManagementReducer);
  const [options, setOptions]: [any, Function] = useState({ a: 1 });

  useEffect(() => {
    if (curProjectInfo.rainfall.state) {
      let myChart = echarts.init(document.querySelector(".echarts-rainfall"));
      window.onresize = function () {
        myChart.resize();
      };
      let arr = curProjectInfo.rainfall.value;
      arr = JSON.parse(arr.replace(/'/g, '"'));
      let rainfallArr: number[] = [];
      let dataArr: string[] = [];
      for (let info of arr) {
        rainfallArr.push(info.rainfall);
        dataArr.push(info.date);
      }
      setOptions({
        ...options,
        title: { text: "月降雨量 (mm/month)" },
        series: [
          {
            data: rainfallArr,
            type: "line",
          },
        ],
        xAxis: {
          type: "category",
          data: dataArr,
        },
        yAxis: {
          type: "value",
        },
      });
      myChart.setOption(options);
    }
  }, [JSON.stringify(options), JSON.stringify(curProjectInfo)]);

  return (
    <RainfallViewBox>
      <Title title="降雨数据" />
      <FileImporter type="rainfall" svg="" />
      {curProjectInfo.rainfall.state && (
        <div
          style={{
            height: "15rem",
            margin: "1rem",
          }}
          className="echarts-rainfall"
        ></div>
      )}
    </RainfallViewBox>
  );
}

export default React.memo(RainfallView);
