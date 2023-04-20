import React from "react";
import styled from "styled-components";
import { useSelector, useDispatch } from "react-redux";
import { InboxOutlined } from "@ant-design/icons";
import type { UploadProps } from "antd";
import { message, Upload } from "antd";
import { updateStatus } from "../../store/features/dataManagementSlice.ts";

const { Dragger } = Upload;
interface IProps {
  type:
    | "rainfall"
    | "DEM"
    | "landuse"
    | "D8"
    | "C_factor"
    | "L_factor"
    | "S_factor";
  svg: any;
}

const FileBox = styled.div`
  /* .drop-area {
    height: 7.5rem;
    width: 90%;
    background: rgb(248, 249, 250);
    margin: 0.5rem auto;
  }
  .drop-area-inner {
    height: 4.5rem;
    width: 80%;
    background: white;
    position: relative;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    border: 0.25rem dashed rgb(222, 226, 230);
    text-align: center;
    line-height: 4.5rem;
  }
  .button {
    margin: 2rem;
  } */
`;

const FileImporter = (props: IProps) => {
  let { curProjectInfo } = useSelector((state) => state.dataManagementReducer);
  let dispatch = useDispatch();
  let draggerProps = {
    name: "file",
    multiple: true,
    action: "",
    directory: false,
    fileList: [],
    onChange(info) {
      const { status } = info.file;
      if (status !== "uploading") {
        console.log(info.file, info.fileList);
      }
      if (status === "done") {
        message.success(`${info.file.name} file uploaded successfully.`);
      } else if (status === "error") {
        message.error(`${info.file.name} file upload failed.`);
      }
    },
    async onDrop(e) {
      const { files } = e.dataTransfer;
      if (files.length == 1) {
        let res = await window.electronAPI.uploadFile({
          filePath: files[0].path,
          type: props.type,
        });
        if (res.status == 200) {
          messageApi.open({
            type: "success",
            content: "上传成功！",
          });
          dispatch(updateStatus(res.msg));
        }
      } else {
        messageApi.open({
          type: "error",
          content: "一次只能上传一个文件，请检查！",
        });
      }
    },
    customRequest(e) {
      return true;
    },
  };
  const [messageApi, contextHolder] = message.useMessage();
  return (
    <FileBox>
      {/* <div className="drop-area">
        <div className="drop-area-inner">
          {curProjectInfo.rainfall.status ? "文件已导入" : "请将文件拖入此处"}
        </div>
      </div>
      <div className="button">
        <Button type="primary">导入文件</Button>
      </div> */}
      <Dragger {...draggerProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">点击此处或者拖拽文件至此处上传文件</p>
        <p className="ant-upload-hint">
          请上传'txt'格式文件，第一行为起始日期，如'20201101'
          ，后续每一行为一天的数据
        </p>
      </Dragger>
      {contextHolder}
    </FileBox>
  );
};

export default FileImporter;