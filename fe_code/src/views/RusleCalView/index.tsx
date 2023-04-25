import React, { useEffect, useMemo, useState } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import { message, Collapse, Button } from "antd";
import * as echarts from "echarts";
import { useSelector } from "react-redux";
interface IConditions {
  imported: string[];
  unimported: string[];
}
const { Panel } = Collapse;
const RusleCalBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;
const PanelBox = styled.div`
  p {
    font-size: 1.3rem;
    font-weight: bold;
    margin-top: 0;
  }
  span {
    font-size: 1.3rem;
    margin-right: 1rem;
  }
`;
type IProps = {};

const RusleCalView = (props: IProps) => {
  const [messageApi, contextHolder] = message.useMessage();
  const [loadings, setLoadings] = useState<boolean[]>([]);
  const [update, setUpdate] = useState(0);
  const { curProjectInfo } = useSelector((state: any) => {
    return state.dataManagementReducer;
  });
  const [loading, setLoading] = useState(false);
  const dataCondition = useMemo(() => {
    let conditions: IConditions = { imported: [], unimported: [] };
    if (curProjectInfo.rainfall.state) {
      conditions.imported.push("R因子");
    } else {
      conditions.unimported.push("R因子");
    }
    if (curProjectInfo.soiltype.state) {
      conditions.imported.push("K因子");
    } else {
      conditions.unimported.push("K因子");
    }
    if (curProjectInfo.rusle.C_factor) {
      conditions.imported.push("C因子");
    } else {
      conditions.unimported.push("C因子");
    }
    if (curProjectInfo.rusle.L_factor) {
      conditions.imported.push("L因子");
    } else {
      conditions.unimported.push("L因子");
    }
    if (curProjectInfo.rusle.S_factor) {
      conditions.imported.push("S因子");
    } else {
      conditions.unimported.push("S因子");
    }

    return conditions;
  }, [JSON.stringify(curProjectInfo)]);
  const rusleCal = async () => {
    setLoading(true);
    let res = await window.electronAPI.rusleCal();
    setLoading(false);
    if (res == "unmatch") {
      messageApi.open({
        type: "error",
        content: "文件栅格数量不匹配，请检查！",
      });
    } else if (res == "err") {
      messageApi.open({
        type: "error",
        content: "计算错误，请检查！",
      });
    } else {
      messageApi.open({
        type: "success",
        content: "计算成功！",
      });
    }
    setUpdate((pre) => pre + 1);
  };
  useEffect(() => {
    const fetchRusle = async () => {
      let res = await window.electronAPI.requireRusle();
      if (res != "err") {
        let myChart = echarts.init(
          document.querySelector(".echarts-rusle") as HTMLElement
        );
        window.onresize = function () {
          myChart.resize();
        };
        let dateArr = res.map((item) => {
          return item.date;
        });
        let rusleArr = res.map((item) => {
          return item.rusle;
        });
        myChart.setOption({
          title: { text: "水土流失量 (kg/month)" },
          series: [
            {
              data: rusleArr,
              type: "line",
            },
          ],
          xAxis: {
            type: "category",
            data: dateArr,
          },
          yAxis: {
            type: "value",
          },
        });
      }
    };
    fetchRusle().catch(console.error);
  }, [update]);

  return (
    <RusleCalBox>
      <Title title="水土流失情况计算" />
      <Collapse size="large" defaultActiveKey={["1"]}>
        <Panel header="查看水土流失数据导入情况" key="1">
          <PanelBox>
            <p>已导入数据</p>
            {dataCondition.imported.length > 0 ? (
              dataCondition.imported.map((item) => {
                return <span key={item}>{item}</span>;
              })
            ) : (
              <span>所有数据均未导入</span>
            )}
            <p style={{ marginTop: "1.5rem" }}>未导入数据</p>
            {dataCondition.unimported.length > 0 ? (
              dataCondition.unimported.map((item) => {
                return <span key={item}>{item}</span>;
              })
            ) : (
              <span>所有数据已导入</span>
            )}
          </PanelBox>
        </Panel>
      </Collapse>
      <Button
        type="primary"
        size="large"
        style={{ width: "12rem", marginTop: "1rem" }}
        onClick={rusleCal}
        loading={loading}
      >
        计算水土流失量
      </Button>
      {curProjectInfo.rainfall.state && (
        <div
          style={{
            height: "15rem",
            margin: "1rem",
          }}
          className="echarts-rusle"
        ></div>
      )}
      {contextHolder}
    </RusleCalBox>
  );
};

export default RusleCalView;
