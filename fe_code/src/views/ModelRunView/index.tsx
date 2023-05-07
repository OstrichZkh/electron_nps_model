import React, { useEffect } from "react";
import styled from "styled-components";
import Title from "../../components/Title";
import { useSelector, useDispatch } from "react-redux";
import { Checkbox, Button, Upload, message } from "antd";
import type { CheckboxChangeEvent } from "antd/es/checkbox";
import { updateStatusAsync } from "../../store/features/dataManagementSlice.ts";

type IProps = {};
type KProps = {
  type: "sed" | "col" | "sedP" | "colP" | "solP" | "TP";
  checked: boolean;
  imported: boolean;
};
const ModelRunBox = styled.div`
  padding: 1rem;
  display: flex;
  flex-direction: column;
`;
const ModelRunView = (props: IProps) => {
  let { curProjectInfo } = useSelector((state) => state.dataManagementReducer);
  // 检查率定数据情况
  useEffect(() => {}, []);
  return (
    <ModelRunBox>
      <Title title="请选择率定目标" />
      {Object.keys(curProjectInfo["observeData"]).map((key) => {
        return (
          <CalibrateSelector
            key={key}
            type={key}
            {...curProjectInfo["observeData"][key]}
          />
        );
      })}
    </ModelRunBox>
  );
};

const CalibrateSelectorBox = styled.div`
  display: flex;
  height: 3rem;
  .check-box {
    align-self: center;
  }
  .check-box-text {
    font-size: 1rem;
  }
  .data-importer {
    align-self: center;
  }
`;
const titleReflect = {
  sed: "泥沙",
  col: "胶体",
  sedP: "大颗粒态磷",
  colP: "胶体磷",
  solP: "溶解态磷",
  TP: "总磷",
};
const CalibrateSelector = (props: KProps) => {
  const [messageApi, contextHolder] = message.useMessage();

  const dispatch = useDispatch();

  const onChange = (e: CheckboxChangeEvent) => {
    dispatch(
      updateStatusAsync([
        {
          target: ["observeData", props.type, "checked"],
          value: e.target.checked,
        },
      ])
    );
  };

  const importData = async (e) => {
    const { originFileObj: targetFile } = e.fileList[0];
    let extension = targetFile.name.split(".")[1];
    if (extension !== "txt") {
      message.error("请上传txt文件！");
      return;
    }
    let respose = await window.electronAPI.uploadFile({
      filePath: targetFile.path,
      type: props.type,
    });
    if (respose.status == 200) {
      message.success("上传成功！");
      return;
    }
  };
  return (
    <CalibrateSelectorBox>
      <div className="check-box">
        <Checkbox defaultChecked={props.checked} onChange={onChange}>
          <div className="check-box-text">{titleReflect[props.type]}</div>
        </Checkbox>
      </div>
      <div className="data-importer">
        <Upload
          beforeUpload={() => false}
          fileList={[]}
          showUploadList={false}
          onChange={importData}
        >
          {props.checked &&
            (props.imported ? (
              <Button danger size="middle">
                删除观测数据
              </Button>
            ) : (
              <Button type="primary" size="middle">
                导入观测数据
              </Button>
            ))}
        </Upload>
      </div>
      {contextHolder}
    </CalibrateSelectorBox>
  );
};

export default ModelRunView;
