import React, { useState } from "react";
import Title from "../../components/Title";
import styled from "styled-components";
import FileImporter from "../../components/FileImporter";
import { useSelector, useDispatch } from "react-redux";
import { Select, Input, Button, message } from "antd";
import { updateStatusAsync } from "../../store/features/dataManagementSlice.ts";

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
    curProjectInfo.landUse.code
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
  const handleCodeChange = (e: any, index: number): void => {
    const { value: inputValue } = e.target;
    luCode[index] = {
      ...luCode[index],
      code: Number(inputValue),
    };
    setLuCode([...luCode]);
  };

  const handleLuChange = (landuse: string, index: number): void => {
    luCode[index] = {
      ...luCode[index],
      type: landuse,
    };
    setLuCode([...luCode]);
    landuseOptions = landuseOptions.map((item) => {
      if (item.value !== landuse) {
        return item;
      } else {
        return { ...item, disabled: true };
      }
    });
    setLanduseOptions(landuseOptions);
  };
  const deleteItem = (idx: number): void => {
    luCode.splice(idx, 1);
    setLuCode([...luCode]);
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
      </DisplayBox>
      {contextHolder}
    </LanduseViewBox>
  );
}

export default LanduseView;
