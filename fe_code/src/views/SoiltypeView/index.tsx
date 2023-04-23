import React, { useEffect, useState } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import FileImporter from "../../components/FileImporter";
import { useSelector, useDispatch } from "react-redux";
import { Select, Input, Button, message, Cascader } from "antd";
import { updateStatusAsync } from "../../store/features/dataManagementSlice.ts";
import * as echarts from "echarts";

interface Option {
  value: string | number;
  label: string;
  children?: Option[];
}
const SoiltypeViewBox = styled.div`
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

function SoiltypeView() {
  const [messageApi, contextHolder] = message.useMessage();
  const dispatch = useDispatch();
  let { curProjectInfo } = useSelector((state) => state.dataManagementReducer);
  let [soiltypeCode, setSoiltypeCode] = useState(
    curProjectInfo.soiltype && curProjectInfo.soiltype.code
      ? curProjectInfo.soiltype.code
      : [
          {
            type: "",
            code: "",
            kValue: "",
          },
        ]
  );
  const options: Option[] = [
    {
      value: "红壤",
      label: "红壤",
      children: [
        { value: "红壤", label: "红壤" },
        { value: "黄红壤", label: "黄红壤" },
        { value: "红壤性土", label: "红壤性土" },
      ],
    },
    {
      value: "黄壤",
      label: "黄壤",
      children: [
        { value: "黄壤", label: "黄壤" },
        { value: "黄壤性土", label: "黄壤性土" },
      ],
    },
    {
      value: "黄棕壤",
      label: "黄棕壤",
      children: [
        { value: "黄棕壤", label: "黄棕壤" },
        { value: "暗黄棕壤", label: "暗黄棕壤" },
        { value: "黄棕壤性土", label: "黄棕壤性土" },
      ],
    },
    {
      value: "黄褐土",
      label: "黄褐土",
      children: [{ value: "黄褐土", label: "黄褐土" }],
    },
    {
      value: "棕壤",
      label: "棕壤",
      children: [{ value: "棕壤", label: "棕壤" }],
    },
    {
      value: "暗棕壤",
      label: "暗棕壤",
      children: [{ value: "暗棕壤", label: "暗棕壤" }],
    },
    {
      value: "石灰土",
      label: "石灰土",
      children: [
        { value: "黑色石灰土", label: "黑色石灰土" },
        { value: "棕色石灰土", label: "棕色石灰土" },
        { value: "黄色石灰土", label: "黄色石灰土" },
      ],
    },
    {
      value: "紫色土",
      label: "紫色土",
      children: [
        { value: "酸性紫色土", label: "酸性紫色土" },
        { value: "中性紫色土", label: "中性紫色土" },
        { value: "石灰紫色土", label: "石灰紫色土" },
      ],
    },
    {
      value: "粗骨土",
      label: "粗骨土",
      children: [
        { value: "酸性粗骨土", label: "酸性粗骨土" },
        { value: "中性粗骨土", label: "中性粗骨土" },
        { value: "钙质粗骨土", label: "钙质粗骨土" },
      ],
    },
    {
      value: "山地草甸土",
      label: "山地草甸土",
      children: [{ value: "山地草甸土", label: "山地草甸土" }],
    },
    {
      value: "水稻土",
      label: "水稻土",
      children: [
        { value: "潴育水稻土", label: "潴育水稻土" },
        { value: "淹育水稻土", label: "淹育水稻土" },
        { value: "渗育水稻土", label: "渗育水稻土" },
        { value: "潜育水稻土", label: "潜育水稻土" },
      ],
    },
  ];
  const kVal = {
    红壤: {
      红壤: 0.0075,
      黄红壤: 0.0077,
      红壤性土: 0.0065,
    },
    黄壤: {
      黄壤: 0.0157,
      黄壤性土: 0.0145,
    },
    黄棕壤: {
      黄棕壤: 0.0168,
      暗黄棕壤: 0.0182,
      黄棕壤性土: 0.0175,
    },
    黄褐土: {
      黄褐土: 0.0192,
    },
    棕壤: {
      棕壤: 0.0072,
    },
    暗棕壤: {
      暗棕壤: 0.0113,
    },
    石灰土: {
      黑色石灰土: 0.0147,
      棕色石灰土: 0.0186,
      黄色石灰土: 0.0167,
    },
    紫色土: {
      酸性紫色土: 0.0196,
      中性紫色土: 0.0179,
      石灰紫色土: 0.0174,
    },
    粗骨土: {
      酸性粗骨土: 0.0055,
      中性粗骨土: 0.0086,
      钙质粗骨土: 0.0097,
    },
    山地草甸土: {
      山地草甸土: 0.0176,
    },
    水稻土: {
      潴育水稻土: 0.0195,
      淹育水稻土: 0.0142,
      渗育水稻土: 0.0186,
      潜育水稻土: 0.0195,
    },
  };
  const hangleSoiltypeChange = (e: any, index: number): void => {
    let k = kVal[e[0]][e[1]];
    let newSoiltypeCode = [...soiltypeCode];
    let newCode = {
      ...newSoiltypeCode[index],
      type: e,
      kValue: Number(k),
    };
    newSoiltypeCode[index] = newCode;
    console.log(soiltypeCode, newSoiltypeCode);
    setSoiltypeCode(newSoiltypeCode);
    message.success("修改成功");
  };

  const handleCodeChange = (e: any, index: number): void => {
    const { value: inputValue } = e.target;
    if (Number.isNaN(+inputValue)) {
      message.error("请输入数字！");
      return;
    }
    let newSoiltypeCode = [...soiltypeCode];
    let newCode = {
      ...newSoiltypeCode[index],
      code: Number(inputValue),
    };
    newSoiltypeCode[index] = newCode;
    setSoiltypeCode([...newSoiltypeCode]);
    message.success("修改成功");
  };
  const deleteItem = (idx: number): void => {
    let newLuCode = soiltypeCode.filter((item, _idx) => {
      return _idx !== idx;
    });
    /* 切忌使用以下方法原地修改状态数组
    luCode.splice(idx, 1); */
    setSoiltypeCode(newLuCode);
  };
  const addItem = (): void => {
    setSoiltypeCode([
      ...soiltypeCode,
      {
        type: "",
        code: "",
      },
    ]);
  };
  const submitItem = (): void => {
    let validate = soiltypeCode.every((item) => {
      return item.type && item.code && typeof item.code == "number";
    });
    console.log(validate);

    if (validate) {
      let payload = [{ target: ["soiltype", "code"], value: soiltypeCode }];
      dispatch(updateStatusAsync(payload));
      message.success(`上传成功！`);
    } else {
      message.error(`格式错误，请检查！`);
    }
  };

  return (
    <SoiltypeViewBox>
      <Title title="土壤类型数据" />
      <FileImporter type="soiltype" svg="" />
      <DisplayBox>
        {soiltypeCode.map((item, index) => {
          return (
            <CodeItemBox key={index}>
              <p>土壤类型{index + 1}</p>
              <Cascader
                onChange={(e) => {
                  hangleSoiltypeChange(e, index);
                }}
                style={{
                  width: 240,
                  margin: "auto 2rem",
                }}
                options={options}
                placeholder="Please select"
                size="large"
                defaultValue={item.type}
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
              <p
                style={{
                  marginLeft: "1rem",
                  width: "6rem",
                }}
              >
                K={item.kValue}
              </p>
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
          // onClick={calLu}
        >
          统计
        </Button>
      </DisplayBox>
      {contextHolder}
    </SoiltypeViewBox>
  );
}

export default SoiltypeView;
