import React, { useEffect, useState } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import FileImporter from "../../components/FileImporter";
import { useSelector, useDispatch } from "react-redux";
import { Select, Input, Button, message } from "antd";
import { updateStatusAsync } from "../../store/features/dataManagementSlice.ts";
import * as echarts from "echarts";

const LanduseViewBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;
const DisplayBox = styled.div`
  margin: 3rem;
  margin-bottom: 1rem;
`;

const CodeItemBox = styled.div`
  display: flex;
  border-top: 1px solid rgb(200, 200, 200);
  font-size: 1.4rem;
`;
function LanduseView() {
  const [messageApi, contextHolder] = message.useMessage();
  const dispatch = useDispatch();
  let { curProjectInfo } = useSelector((state) => state.dataManagementReducer);
  let [luCode, setLuCode] = useState(
    curProjectInfo.landUse && curProjectInfo.landUse.code
      ? curProjectInfo.landUse.code
      : [
          {
            type: "",
            code: "",
          },
        ]
  );
  let [landuseOptions, setLanduseOptions] = useState([
    { value: "forest", label: "林地" },
    { value: "paddy", label: "水田" },
    { value: "water", label: "水体" },
    { value: "sloping", label: "坡耕地" },
    { value: "construct", label: "建设用地" },
  ]);
  let [echartsOptions, setEchartsOptions]: [any, any] = useState();
  const handleCodeChange = (e: any, index: number): void => {
    const { value: inputValue } = e.target;
    if (Number.isNaN(+inputValue)) {
      message.error("请输入数字！");
      return;
    }
    let newLuCode = [...luCode];
    let newCode = {
      ...newLuCode[index],
      code: Number(inputValue),
    };

    newLuCode[index] = newCode;
    setLuCode([...newLuCode]);
    message.success("修改成功");
  };
  const handleLuChange = (landuse: string, index: number): void => {
    luCode[index] = {
      ...luCode[index],
      type: landuse,
    };
    setLuCode([...luCode]);
  };
  const deleteItem = (idx: number): void => {
    let newLuCode = luCode.filter((item, _idx) => {
      return _idx !== idx;
    });
    /* 切忌使用以下方法原地修改状态数组
    luCode.splice(idx, 1); */
    setLuCode(newLuCode);
  };
  const addItem = (): void => {
    setLuCode([
      ...luCode,
      {
        type: "",
        code: "",
      },
    ]);
  };
  const submitItem = (): void => {
    let validate = luCode.every((item) => {
      return item.type && item.code && typeof item.code == "number";
    });
    if (validate) {
      let payload = [{ target: ["landUse", "code"], value: luCode }];
      dispatch(updateStatusAsync(payload));
      message.success(`上传成功！`);
    } else {
      message.error(`格式错误，请检查！`);
    }
  };
  const calLu = (): void => {
    if (
      !curProjectInfo.landUse ||
      !Array.isArray(curProjectInfo.landUse.code)
    ) {
      return;
    }
    let validate = curProjectInfo.landUse.code.every((item) => {
      return (
        Object.keys(curProjectInfo.landUse.counts).indexOf(item.code + "") !==
        -1
      );
    });

    if (!validate) {
      message.error("请检查tif文件与表格内编号是否匹配！");
    } else {
      const options = curProjectInfo.landUse.code.map((item, index) => {
        let name: string;
        switch (item.type) {
          case "forest":
            name = "林地";
            break;
          case "paddy":
            name = "水田";
            break;
          case "water":
            name = "水体";
            break;
          case "sloping":
            name = "坡耕地";
            break;
          case "construct":
            name = "建设用地";
            break;
        }

        return {
          value: curProjectInfo.landUse.counts[item.code],
          name: name,
        };
      });

      setEchartsOptions({
        title: {
          text: "土地利用类型",
          left: "center",
          top: "center",
        },
        series: [
          {
            type: "pie",
            data: options,
            radius: ["40%", "70%"],
          },
        ],
      });
    }
  };
  useEffect(() => {
    if (echartsOptions) {
      let myChart = echarts.init(
        document.querySelector(".echarts-landuse") as HTMLElement
      );
      window.onresize = function () {
        myChart.resize();
      };
      myChart.setOption(echartsOptions);
    }
  }, [JSON.stringify(echartsOptions)]);

  useEffect(() => {
    calLu();
  }, []);

  return (
    <LanduseViewBox>
      <Title title="土地利用类型数据" />
      <FileImporter type="landuse" svg="" />
      <DisplayBox>
        {luCode.map((item, index) => {
          return (
            <CodeItemBox key={index}>
              <p>土地利用类型{index + 1}</p>
              <Select
                defaultValue={item.type}
                style={{
                  width: 240,
                  margin: "auto 2rem",
                }}
                size="large"
                onChange={(e) => {
                  handleLuChange(e, index);
                }}
                options={landuseOptions}
              />
              <Input
                style={{
                  width: 240,
                  margin: "auto 0rem",
                }}
                defaultValue={item.code}
                size="large"
                onChange={(e) => {
                  handleCodeChange(e, index);
                }}
              />
              <Button
                type="primary"
                style={{
                  width: 120,
                  fontSize: "1.2rem",
                  lineHeight: "100%",
                  margin: "auto 2rem",
                }}
                size="large"
                danger
                onClick={() => {
                  deleteItem(index);
                }}
              >
                删除
              </Button>
            </CodeItemBox>
          );
        })}

        <Button
          style={{
            width: 120,
            fontSize: "1.2rem",
            lineHeight: "100%",
            margin: "auto 1rem",
          }}
          size="large"
          type="primary"
          onClick={addItem}
        >
          新增
        </Button>
        <Button
          style={{
            width: 120,
            fontSize: "1.2rem",
            lineHeight: "100%",
            margin: "auto 1rem",
          }}
          size="large"
          onClick={submitItem}
        >
          提交
        </Button>
        <Button
          style={{
            width: 120,
            fontSize: "1.2rem",
            lineHeight: "100%",
            margin: "auto 1rem",
          }}
          size="large"
          onClick={calLu}
        >
          统计
        </Button>
      </DisplayBox>
      <div
        style={{
          height: "20rem",
          width: "30rem",
          margin: "1rem",
        }}
        className="echarts-landuse"
      ></div>
      {contextHolder}
    </LanduseViewBox>
  );
}

export default LanduseView;
